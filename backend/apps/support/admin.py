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
    readonly_fields = ('ticket_id', 'ai_category', 'ai_priority', 'ai_suggested_response', 'created_at', 'updated_at')
    inlines = [TicketMessageInline]