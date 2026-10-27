from pathlib import Path

from rest_framework import serializers
from django.urls import reverse
from .models import Ticket, TicketMessage
from apps.accounts.serializers import UserSerializer
from apps.books.serializers import BookListSerializer

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024
ALLOWED_ATTACHMENT_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.txt'}


def validate_ticket_attachment(upload):
    extension = Path(upload.name).suffix.lower()
    if upload.size > MAX_ATTACHMENT_SIZE:
        raise serializers.ValidationError('Attachment must be 5 MB or smaller.')
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise serializers.ValidationError(
            'Upload a PDF, PNG, JPEG, or plain-text file.'
        )

    upload.seek(0)
    header = upload.read(16)
    upload.seek(0)
    if extension == '.pdf' and not header.startswith(b'%PDF-'):
        raise serializers.ValidationError('The file is not a valid PDF.')
    if extension == '.png' and not header.startswith(b'\x89PNG\r\n\x1a\n'):
        raise serializers.ValidationError('The file is not a valid PNG image.')
    if extension in {'.jpg', '.jpeg'} and not header.startswith(b'\xff\xd8\xff'):
        raise serializers.ValidationError('The file is not a valid JPEG image.')
    if extension == '.txt':
        try:
            upload.read().decode('utf-8')
        except UnicodeDecodeError as exc:
            raise serializers.ValidationError(
                'Plain-text attachments must be UTF-8 encoded.'
            ) from exc
        finally:
            upload.seek(0)
    return upload


class TicketMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for threaded conversation messages inside a ticket.
    """
    sender = UserSerializer(read_only=True)
    message = serializers.CharField(max_length=10000)

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

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Message content is required.')
        return value


class TicketListSerializer(serializers.ModelSerializer):
    """
    Compact list serializer for tickets overview tables.
    """
    author_name = serializers.CharField(source='author.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    book_title = serializers.CharField(source='book.title', read_only=True, allow_null=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_id',
            'subject',
            'author_name',
            'book_title',
            'category',
            'category_display',
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
    attachment_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    ai_category_display = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_id',
            'subject',
            'description',
            'author',
            'book',
            'attachment_url',
            'category',
            'category_display',
            'priority',
            'status',
            'assigned_to',
            'ai_category',
            'ai_category_display',
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

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and not request.user.is_admin_user:
            for field in fields.values():
                field.read_only = True
            fields.pop('internal_notes', None)
            for name in ('ai_category', 'ai_category_display', 'ai_priority', 'ai_suggested_response'):
                fields.pop(name, None)
        return fields

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return None
        request = self.context.get('request')
        url = reverse('ticket_attachment_download', kwargs={'pk': obj.pk})
        return request.build_absolute_uri(url) if request else url

    def get_ai_category_display(self, obj):
        return obj.get_ai_category_display() if obj.ai_category else None


class TicketCreateSerializer(serializers.ModelSerializer):
    """
    Author ticket creation serializer.
    """
    attachment = serializers.FileField(
        required=False,
        allow_null=True,
        write_only=True,
        validators=[validate_ticket_attachment],
    )
    description = serializers.CharField(max_length=10000)
    ticket_id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    attachment_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_id',
            'book',
            'subject',
            'description',
            'attachment',
            'attachment_url',
            'category',
            'category_display',
            'priority',
            'status',
            'created_at',
            'updated_at',
        ]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request:
            fields['book'].queryset = fields['book'].queryset.filter(
                author=request.user
            )
        return fields

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return None
        request = self.context.get('request')
        url = reverse('ticket_attachment_download', kwargs={'pk': obj.pk})
        return request.build_absolute_uri(url) if request else url

    def validate_subject(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Subject is required.')
        return value

    def validate_description(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Description is required.')
        return value
