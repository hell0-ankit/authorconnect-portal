from django.contrib import admin
from .models import Ticket, TicketMessage

class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'subject', 'author', 'category', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('subject', 'author__username', 'description')
    inlines = [TicketMessageInline]