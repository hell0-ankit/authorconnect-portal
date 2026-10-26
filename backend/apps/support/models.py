import uuid
from django.db import models
from django.conf import settings
from apps.books.models import Book


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Category(models.TextChoices):
        ROYALTY = 'ROYALTY', 'Royalty & Payouts'
        PUBLISHING = 'PUBLISHING', 'Publishing & Editorial'
        DISTRIBUTION = 'DISTRIBUTION', 'Distribution & Sales'
        ACCOUNT = 'ACCOUNT', 'Account & General Support'
        TECHNICAL = 'TECHNICAL', 'Technical Issue'

    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        help_text="Optional: If ticket is related to a specific book"
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()

    # Active values (Admin override kar sakta hai)
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.ACCOUNT
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    # AI Integration Fields
    ai_category = models.CharField(max_length=50, blank=True, null=True)
    ai_priority = models.CharField(max_length=20, blank=True, null=True)
    ai_suggested_response = models.TextField(blank=True, null=True)

    internal_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{str(self.ticket_id)[:8]} - {self.subject}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message = models.TextField()
    is_internal_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.username} on Ticket #{str(self.ticket.ticket_id)[:8]}"