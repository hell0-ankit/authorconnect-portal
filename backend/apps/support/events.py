import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def ticket_group_name(ticket_id):
    return f'ticket_{ticket_id}'


def serialize_ticket_message(message):
    return {
        'type': 'ticket_message',
        'id': message.pk,
        'ticket_id': message.ticket_id,
        'sender': {
            'id': message.sender_id,
            'username': message.sender.username,
            'role': message.sender.role,
        },
        'message': message.message,
        'is_internal_note': message.is_internal_note,
        'created_at': message.created_at.isoformat(),
    }


def _send_event(group, event):
    layer = get_channel_layer()
    if layer is None:
        logger.error('Ticket event was persisted but no channel layer is configured.')
        return False
    try:
        async_to_sync(layer.group_send)(group, event)
    except Exception:
        logger.exception('Ticket event delivery failed for group %s.', group)
        return False
    return True


def broadcast_ticket_message(message):
    if message.is_internal_note:
        return True
    return _send_event(
        ticket_group_name(message.ticket_id),
        {'type': 'ticket.message', 'payload': serialize_ticket_message(message)},
    )


def broadcast_new_ticket(ticket):
    return _send_event(
        'admin_ticket_queue',
        {
            'type': 'ticket.new',
            'payload': {
                'type': 'new_ticket',
                'id': ticket.pk,
                'ticket_id': str(ticket.ticket_id),
                'subject': ticket.subject,
                'author_name': ticket.author.username,
                'book_title': ticket.book.title if ticket.book_id else None,
                'category': ticket.category,
                'category_display': ticket.get_category_display(),
                'priority': ticket.priority,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat(),
            },
        },
    )


def broadcast_ticket_update(ticket):
    payload = {
        'type': 'ticket_update',
        'id': ticket.pk,
        'category': ticket.category,
        'category_display': ticket.get_category_display(),
        'priority': ticket.priority,
        'status': ticket.status,
        'updated_at': ticket.updated_at.isoformat(),
    }
    event = {'type': 'ticket.updated', 'payload': payload}
    ticket_delivered = _send_event(ticket_group_name(ticket.pk), event)
    admin_delivered = _send_event('admin_ticket_queue', event)
    return ticket_delivered and admin_delivered
