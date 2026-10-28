from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import Ticket, TicketMessage
from .events import broadcast_new_ticket, broadcast_ticket_message, broadcast_ticket_update
from .serializers import (
    TicketListSerializer,
    TicketDetailSerializer,
    TicketCreateSerializer,
    TicketMessageSerializer,
)
from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsAdminUserRole
from services.ai_service import generate_ticket_response_draft


@extend_schema(tags=['Support Tickets'])
class TicketListCreateView(generics.ListCreateAPIView):
    """
    - GET: List tickets (Admin sees all; Author sees only own tickets).
    - POST: Author creates a ticket for admin review.
    """
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related('author', 'assigned_to', 'book').all()

        # Role-based scoping
        if not user.is_admin_user:
            queryset = queryset.filter(author=user)
        else:
            status_param = self.request.query_params.get('status')
            category_param = self.request.query_params.get('category')
            priority_param = self.request.query_params.get('priority')
            if status_param:
                queryset = queryset.filter(status=status_param.upper())
            if category_param:
                queryset = queryset.filter(category=category_param.upper())
            if priority_param:
                queryset = queryset.filter(priority=priority_param.upper())

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        description = serializer.validated_data.get('description')

        ticket = serializer.save(author=self.request.user)

        # Initial author message in conversation thread
        TicketMessage.objects.create(
            ticket=ticket,
            sender=self.request.user,
            message=description,
            is_internal_note=False
        )
        broadcast_new_ticket(ticket)


@extend_schema(tags=['Support Tickets'])
class TicketDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update ticket details:
    - Author: Read-only access to own ticket.
    - Admin: Can update status, priority, category, assignment, and internal notes.
    """
    serializer_class = TicketDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Ticket.objects.select_related('author', 'assigned_to', 'book').all()
        return Ticket.objects.filter(author=user).select_related('author', 'assigned_to', 'book')

    def perform_update(self, serializer):
        ticket = serializer.instance
        previous = (ticket.status, ticket.category, ticket.priority)
        ticket = serializer.save()
        current = (ticket.status, ticket.category, ticket.priority)
        if current != previous:
            broadcast_ticket_update(ticket)


@extend_schema(tags=['Support Tickets'])
class TicketMessageCreateView(generics.CreateAPIView):
    """
    Add a message or reply to a ticket thread.
    """
    serializer_class = TicketMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('pk')
        user = self.request.user

        if user.is_admin_user:
            ticket = get_object_or_404(Ticket, pk=ticket_id)
        else:
            ticket = get_object_or_404(Ticket, pk=ticket_id, author=user)

        is_internal = serializer.validated_data.get('is_internal_note', False)
        # Authors cannot create internal admin notes
        if not user.is_admin_user:
            is_internal = False

        message = serializer.save(
            ticket=ticket,
            sender=user,
            is_internal_note=is_internal
        )
        self.message_broadcasted = broadcast_ticket_message(message)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if getattr(self, 'message_broadcasted', True) is False:
            response.data['delivery_warning'] = (
                'Your reply was saved, but live delivery is currently unavailable. '
                'Other participants will see it when they reconnect or refresh.'
            )
        return response


@extend_schema(tags=['Support Tickets'])
class TicketAIDraftView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def post(self, request, pk):
        ticket = get_object_or_404(
            Ticket.objects.select_related('author', 'book'),
            pk=pk,
        )
        book_context = ''
        book_title = None
        pending_royalty = None
        if ticket.book_id:
            book_title = ticket.book.title
            pending_royalty = ticket.book.royalty_pending
            book_context = (
                f'Title: {ticket.book.title}; ISBN: {ticket.book.isbn or "not provided"}; '
                f'Genre: {ticket.book.genre or "not provided"}; '
                f'Publication status: {ticket.book.status}; '
                f'Pending royalty: Rs {ticket.book.royalty_pending}.'
            )
        conversation_context = '\n'.join(
            f"{'Author' if message.sender_id == ticket.author_id else 'Support'}: "
            f"{message.message}"
            for message in ticket.messages.filter(
                is_internal_note=False,
            ).select_related('sender')
        )
        draft = generate_ticket_response_draft(
            ticket.subject,
            ticket.description,
            book_context,
            book_title=book_title,
            pending_royalty=pending_royalty,
            conversation_context=conversation_context,
        )
        if draft is None:
            return Response(
                {'detail': 'AI drafting is unavailable. You can write and send a manual reply.'},
                status=503,
            )
        return Response({'draft': draft})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_attachment_download(request, pk):
    user = request.user
    tickets = Ticket.objects.filter(pk=pk)
    if not user.is_admin_user:
        tickets = tickets.filter(author=user)
    ticket = get_object_or_404(tickets)
    if not ticket.attachment:
        raise NotFound('This ticket has no attachment.')

    ticket.attachment.open('rb')
    return FileResponse(
        ticket.attachment,
        as_attachment=True,
        filename=ticket.attachment.name.rsplit('/', 1)[-1],
    )