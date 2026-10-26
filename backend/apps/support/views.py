from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Ticket, TicketMessage
from .serializers import (
    TicketListSerializer,
    TicketDetailSerializer,
    TicketCreateSerializer,
    TicketMessageSerializer,
)
from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsAdminUserRole
from services.ai_service import analyze_ticket_with_ai


@extend_schema(tags=['Support Tickets'])
class TicketListCreateView(generics.ListCreateAPIView):
    """
    - GET: List tickets (Admin sees all; Author sees only own tickets).
    - POST: Author creates ticket, automatically analyzed via AI service.
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
        subject = serializer.validated_data.get('subject')
        description = serializer.validated_data.get('description')

        # Trigger AI analysis
        ai_data = analyze_ticket_with_ai(subject, description)

        ticket = serializer.save(
            author=self.request.user,
            category=ai_data.get('category', Ticket.Category.ACCOUNT),
            priority=ai_data.get('priority', Ticket.Priority.MEDIUM),
            ai_category=ai_data.get('category'),
            ai_priority=ai_data.get('priority'),
            ai_suggested_response=ai_data.get('suggested_response'),
        )

        # Initial author message in conversation thread
        TicketMessage.objects.create(
            ticket=ticket,
            sender=self.request.user,
            message=description,
            is_internal_note=False
        )


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

        serializer.save(
            ticket=ticket,
            sender=user,
            is_internal_note=is_internal
        )