from django.urls import path
from .views import (
    TicketListCreateView,
    TicketDetailView,
    TicketMessageCreateView,
    TicketAIDraftView,
    ticket_attachment_download,
)

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('<int:pk>/attachment/', ticket_attachment_download, name='ticket_attachment_download'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/messages/', TicketMessageCreateView.as_view(), name='ticket_message_create'),
    path('<int:pk>/ai-draft/', TicketAIDraftView.as_view(), name='ticket_ai_draft'),
]