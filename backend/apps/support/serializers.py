from rest_framework import serializers
from .models import Ticket, TicketMessage
from apps.accounts.serializers import UserSerializer
from apps.books.serializers import BookListSerializer


class TicketMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for threaded conversation messages inside a ticket.
    """
    sender = UserSerializer(read_only=True)

    class Meta:
        model = TicketMessage
        fields = [
            'id',
            'ticket',
            'sender',
            'message',
            'is_internal_note',
            'created_at',
        ]
        read_only_fields = ['id', 'ticket', 'sender', 'created_at']


class TicketListSerializer(serializers.ModelSerializer):
    """
    Compact list serializer for tickets overview tables.
    """
    author_name = serializers.CharField(source='author.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    book_title = serializers.CharField(source='book.title', read_only=True, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'subject',
            'author_name',
            'book_title',
            'category',
            'priority',
            'status',
            'assigned_to_name',
            'created_at',
            'updated_at',
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    """
    Full detail serializer including conversation thread, AI classification, and internal notes.
    """
    author = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id',
            'subject',
            'description',
            'author',
            'book',
            'category',
            'priority',
            'status',
            'assigned_to',
            'ai_category',
            'ai_priority',
            'ai_suggested_response',
            'internal_notes',
            'created_at',
            'updated_at',
            'messages',
        ]
        read_only_fields = [
            'id',
            'author',
            'ai_category',
            'ai_priority',
            'ai_suggested_response',
            'created_at',
            'updated_at',
        ]

    def get_messages(self, obj):
        # Authors cannot see internal admin notes
        user = self.context.get('request').user
        messages_qs = obj.messages.select_related('sender').all()
        if not user.is_admin_user:
            messages_qs = messages_qs.filter(is_internal_note=False)
        return TicketMessageSerializer(messages_qs, many=True).data


class TicketCreateSerializer(serializers.ModelSerializer):
    """
    Author ticket creation serializer.
    """
    class Meta:
        model = Ticket
        fields = [
            'id',
            'book',
            'subject',
            'description',
        ]