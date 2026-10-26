from django.urls import path
from .views import TicketListCreateView, TicketDetailView, TicketMessageCreateView

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/messages/', TicketMessageCreateView.as_view(), name='ticket_message_create'),
]