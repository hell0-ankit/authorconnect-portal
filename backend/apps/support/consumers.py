import asyncio
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .auth import get_user_for_token
from .events import serialize_ticket_message, ticket_group_name
from .models import Ticket, TicketMessage

logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 10000


@database_sync_to_async
def _ticket_access(ticket_id, user):
    try:
        ticket = Ticket.objects.only('id', 'author_id').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return None
    return user.is_admin_user or ticket.author_id == user.pk


@database_sync_to_async
def _save_ticket_message(ticket_id, user, text):
    ticket = Ticket.objects.get(pk=ticket_id)
    return TicketMessage.objects.create(
        ticket=ticket,
        sender=user,
        message=text,
        is_internal_note=False,
    )


class JWTAuthenticatedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.authenticated = False
        self.authentication_expired = False
        await self.accept()
        await self.send_json({'type': 'auth_required'})
        self.authentication_timeout = asyncio.create_task(
            self._close_if_unauthenticated()
        )

    async def _close_if_unauthenticated(self):
        await asyncio.sleep(5)
        if not self.authenticated:
            self.authentication_expired = True
            await self.close(code=4401)

    async def authenticate(self, content):
        if not isinstance(content, dict) or content.get('type') != 'authenticate':
            await self.close(code=4401)
            return False
        raw_token = content.get('token')
        if not isinstance(raw_token, str) or not raw_token or len(raw_token) > 4096:
            await self.close(code=4401)
            return False
        user = await get_user_for_token(raw_token)
        if (
            self.authentication_expired
            or isinstance(user, AnonymousUser)
            or not user.is_authenticated
        ):
            await self.close(code=4401)
            return False
        self.scope['user'] = user
        self.user = user
        self.authenticated = True
        self.authentication_timeout.cancel()
        return True

    async def disconnect(self, close_code):
        if hasattr(self, 'authentication_timeout') and not self.authentication_timeout.done():
            self.authentication_timeout.cancel()


class TicketConsumer(JWTAuthenticatedConsumer):
    async def receive_json(self, content, **kwargs):
        if not self.authenticated:
            if not await self.authenticate(content):
                return
            access = await _ticket_access(
                self.scope['url_route']['kwargs']['ticket_id'],
                self.user,
            )
            if access is not True:
                close_code = 4404 if access is None and self.user.is_admin_user else 4403
                await self.close(code=close_code)
                return
            self.ticket_id = int(self.scope['url_route']['kwargs']['ticket_id'])
            self.ticket_group = ticket_group_name(self.ticket_id)
            try:
                await self.channel_layer.group_add(self.ticket_group, self.channel_name)
            except Exception:
                logger.exception('Could not subscribe to ticket updates.')
                await self.close(code=1013)
                return
            await self.send_json({'type': 'connection', 'status': 'connected'})
            return

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        await self.receive_message(content)

    async def receive_message(self, content):
        if not isinstance(content, dict) or content.get('type') != 'message':
            await self.send_json({
                'type': 'error',
                'code': 'invalid_event',
                'message': 'Send a message event with a message field.',
            })
            return

        text = content.get('message')
        if not isinstance(text, str) or not text.strip():
            await self.send_json({
                'type': 'error',
                'code': 'invalid_message',
                'message': 'Message content is required.',
            })
            return
        text = text.strip()
        if len(text) > MAX_MESSAGE_LENGTH:
            await self.send_json({
                'type': 'error',
                'code': 'message_too_long',
                'message': f'Messages must be {MAX_MESSAGE_LENGTH} characters or fewer.',
            })
            return

        message = await _save_ticket_message(
            self.ticket_id,
            self.user,
            text,
        )
        payload = serialize_ticket_message(message)
        try:
            await self.channel_layer.group_send(
                self.ticket_group,
                {'type': 'ticket.message', 'payload': payload},
            )
        except Exception:
            logger.exception(
                'Ticket message %s was saved but could not be broadcast.',
                message.pk,
            )
            await self.send_json({
                'type': 'error',
                'code': 'delivery_unavailable',
                'message': 'Message saved; live delivery is unavailable. Reload the conversation to sync.',
            })

    async def disconnect(self, close_code):
        await super().disconnect(close_code)
        if not hasattr(self, 'ticket_group'):
            return
        try:
            await self.channel_layer.group_discard(self.ticket_group, self.channel_name)
        except Exception:
            logger.warning('Could not clean up ticket WebSocket groups.')

    async def ticket_message(self, event):
        await self.send_json(event['payload'])

    async def ticket_updated(self, event):
        await self.send_json(event['payload'])


class AdminTicketQueueConsumer(JWTAuthenticatedConsumer):
    async def receive_json(self, content, **kwargs):
        if not self.authenticated:
            if not await self.authenticate(content):
                return
            if not self.user.is_admin_user:
                await self.close(code=4403)
                return
            try:
                await self.channel_layer.group_add(
                    'admin_ticket_queue',
                    self.channel_name,
                )
            except Exception:
                logger.exception('Could not subscribe to the admin ticket queue.')
                await self.close(code=1013)
                return
            await self.send_json({'type': 'connection', 'status': 'connected'})
            return

        await self.send_json({
            'type': 'error',
            'code': 'invalid_event',
            'message': 'The admin ticket queue is read-only.',
        })

    async def disconnect(self, close_code):
        await super().disconnect(close_code)
        if not self.authenticated:
            return
        try:
            await self.channel_layer.group_discard(
                'admin_ticket_queue',
                self.channel_name,
            )
        except Exception:
            logger.warning('Could not clean up the admin ticket queue WebSocket.')

    async def ticket_new(self, event):
        await self.send_json(event['payload'])

    async def ticket_updated(self, event):
        await self.send_json(event['payload'])
