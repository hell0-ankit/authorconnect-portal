from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.books.models import Book
from apps.support.models import Ticket, TicketMessage
from config.asgi import application

User = get_user_model()
TEST_CHANNEL_LAYERS = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}


@override_settings(
    ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'],
    CHANNEL_LAYERS=TEST_CHANNEL_LAYERS,
)
class TicketWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='socket_admin',
            email='socket-admin@example.com',
            password='test-password',
            role=User.Role.ADMIN,
        )
        self.author = User.objects.create_user(
            username='socket_author',
            email='socket-author@example.com',
            password='test-password',
            role=User.Role.AUTHOR,
        )
        self.other_author = User.objects.create_user(
            username='other_author',
            email='other-author@example.com',
            password='test-password',
            role=User.Role.AUTHOR,
        )
        self.book = Book.objects.create(
            author=self.author,
            title='Realtime Support',
            isbn='978-1-00000-000-1',
        )
        self.ticket = Ticket.objects.create(
            author=self.author,
            book=self.book,
            subject='WebSocket support',
            description='Please help me.',
        )

    def _token(self, user):
        return str(AccessToken.for_user(user))

    def _communicator(self, path):
        return WebsocketCommunicator(
            application,
            path,
            headers=[(b'origin', b'http://localhost:5173')],
        )

    async def _authenticate(self, communicator, user):
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual(
            await communicator.receive_json_from(),
            {'type': 'auth_required'},
        )
        await communicator.send_json_to({
            'type': 'authenticate',
            'token': self._token(user),
        })
        return await communicator.receive_json_from()

    def test_author_and_admin_can_connect_and_exchange_persisted_messages(self):
        async def scenario():
            path = f'/ws/tickets/{self.ticket.pk}/'
            author_socket = self._communicator(path)
            admin_socket = self._communicator(path)
            try:
                author_connected = await self._authenticate(author_socket, self.author)
                admin_connected = await self._authenticate(admin_socket, self.admin)
                self.assertEqual(author_connected['status'], 'connected')
                self.assertEqual(admin_connected['status'], 'connected')

                await author_socket.send_json_to({
                    'type': 'message',
                    'message': 'Can you share an update?',
                })
                author_event = await author_socket.receive_json_from()
                admin_event = await admin_socket.receive_json_from()
                self.assertEqual(author_event, admin_event)
                self.assertEqual(author_event['type'], 'ticket_message')
                self.assertEqual(author_event['message'], 'Can you share an update?')
                self.assertEqual(author_event['sender']['id'], self.author.pk)
                return author_event['id']
            finally:
                await author_socket.disconnect()
                await admin_socket.disconnect()

        message_id = async_to_sync(scenario)()
        message = TicketMessage.objects.get(pk=message_id)
        self.assertEqual(message.ticket_id, self.ticket.pk)
        self.assertEqual(message.sender_id, self.author.pk)
        self.assertFalse(message.is_internal_note)

    def test_author_cannot_connect_to_another_authors_ticket(self):
        async def scenario():
            communicator = self._communicator(f'/ws/tickets/{self.ticket.pk}/')
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.receive_json_from()
            await communicator.send_json_to({
                'type': 'authenticate',
                'token': self._token(self.other_author),
            })
            closed = await communicator.receive_output()
            self.assertEqual(closed['type'], 'websocket.close')
            self.assertEqual(closed['code'], 4403)

        async_to_sync(scenario)()

    def test_invalid_jwt_is_rejected_without_joining_ticket_group(self):
        async def scenario():
            communicator = self._communicator(f'/ws/tickets/{self.ticket.pk}/')
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.receive_json_from()
            await communicator.send_json_to({
                'type': 'authenticate',
                'token': 'not-a-valid-jwt',
            })
            closed = await communicator.receive_output()
            self.assertEqual(closed['type'], 'websocket.close')
            self.assertEqual(closed['code'], 4401)

        async_to_sync(scenario)()

    def test_admin_gets_not_found_for_missing_ticket(self):
        async def scenario():
            communicator = self._communicator('/ws/tickets/999999/')
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.receive_json_from()
            await communicator.send_json_to({
                'type': 'authenticate',
                'token': self._token(self.admin),
            })
            closed = await communicator.receive_output()
            self.assertEqual(closed['type'], 'websocket.close')
            self.assertEqual(closed['code'], 4404)

        async_to_sync(scenario)()

    def test_invalid_websocket_message_is_not_persisted(self):
        async def scenario():
            communicator = self._communicator(f'/ws/tickets/{self.ticket.pk}/')
            try:
                await self._authenticate(communicator, self.author)
                await communicator.send_json_to({
                    'type': 'message',
                    'message': '   ',
                })
                event = await communicator.receive_json_from()
                self.assertEqual(event['code'], 'invalid_message')
            finally:
                await communicator.disconnect()

        async_to_sync(scenario)()
        self.assertFalse(TicketMessage.objects.filter(ticket=self.ticket).exists())

    def test_admin_can_receive_new_ticket_queue_events(self):
        async def scenario():
            communicator = self._communicator('/ws/tickets/queue/')
            try:
                connected = await self._authenticate(communicator, self.admin)
                self.assertEqual(connected['status'], 'connected')
                await get_channel_layer().group_send(
                    'admin_ticket_queue',
                    {
                        'type': 'ticket.new',
                        'payload': {
                            'type': 'new_ticket',
                            'id': self.ticket.pk,
                            'subject': self.ticket.subject,
                        },
                    },
                )
                event = await communicator.receive_json_from()
                self.assertEqual(event['type'], 'new_ticket')
                self.assertEqual(event['id'], self.ticket.pk)
                self.assertEqual(event['subject'], self.ticket.subject)
            finally:
                await communicator.disconnect()

        async_to_sync(scenario)()

    def test_author_cannot_subscribe_to_admin_queue(self):
        async def scenario():
            communicator = self._communicator('/ws/tickets/queue/')
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.receive_json_from()
            await communicator.send_json_to({
                'type': 'authenticate',
                'token': self._token(self.author),
            })
            closed = await communicator.receive_output()
            self.assertEqual(closed['type'], 'websocket.close')
            self.assertEqual(closed['code'], 4403)

        async_to_sync(scenario)()
