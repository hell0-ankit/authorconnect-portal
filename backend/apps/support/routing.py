from django.urls import re_path

from .consumers import AdminTicketQueueConsumer, TicketConsumer

websocket_urlpatterns = [
    re_path(
        r'^ws/tickets/queue/$',
        AdminTicketQueueConsumer.as_asgi(),
    ),
    re_path(
        r'^ws/tickets/(?P<ticket_id>\d+)/$',
        TicketConsumer.as_asgi(),
    ),
]
