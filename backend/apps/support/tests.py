from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from apps.books.models import Book
from apps.support.models import Ticket, TicketMessage

User = get_user_model()
TEST_CHANNEL_LAYERS = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
class AuthorConnectAPITests(APITestCase):
    def setUp(self):
        # 1. Setup Admin user
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True
        )

        # 2. Setup Author 1
        self.author1 = User.objects.create_user(
            username='author_one',
            email='author1@test.com',
            password='Password123!',
            role=User.Role.AUTHOR
        )

        # 3. Setup Author 2
        self.author2 = User.objects.create_user(
            username='author_two',
            email='author2@test.com',
            password='Password123!',
            role=User.Role.AUTHOR
        )

        # 4. Setup Books
        self.book1 = Book.objects.create(
            author=self.author1,
            title='The Quantum Realm',
            isbn='978-1-23456-789-0',
            genre='Sci-Fi',
            mrp=499.00,
            sales_count=120,
            royalty_earned=12000.00,
            royalty_paid=8000.00,
            royalty_pending=4000.00,
            status=Book.Status.PUBLISHED
        )

        self.book2 = Book.objects.create(
            author=self.author2,
            title='Echoes of Silence',
            isbn='978-0-98765-432-1',
            genre='Poetry',
            mrp=299.00,
            sales_count=50,
            royalty_earned=3000.00,
            royalty_paid=3000.00,
            royalty_pending=0.00,
            status=Book.Status.PUBLISHED
        )

    def test_author_authentication_and_login(self):
        url = reverse('auth_login')
        payload = {
            'username': 'author_one',
            'password': 'Password123!'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['role'], 'AUTHOR')

    def test_books_isolation_author_cannot_see_other_author_books(self):
        self.client.force_authenticate(user=self.author1)
        url = reverse('book_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Author 1 should only see their own book
        book_ids = [b['id'] for b in response.data['results']]
        self.assertIn(self.book1.id, book_ids)
        self.assertNotIn(self.book2.id, book_ids)
        author_book = next(book for book in response.data['results'] if book['id'] == self.book1.id)
        self.assertEqual(str(author_book['royalty_earned']), '12000.00')
        self.assertEqual(str(author_book['royalty_paid']), '8000.00')
        self.assertEqual(str(author_book['royalty_pending']), '4000.00')

    def test_admin_can_see_all_books(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('book_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        book_ids = [b['id'] for b in response.data['results']]
        self.assertIn(self.book1.id, book_ids)
        self.assertIn(self.book2.id, book_ids)

    def test_author_create_ticket_without_running_ai(self):
        self.client.force_authenticate(user=self.author1)
        url = reverse('ticket_list_create')
        payload = {
            'book': self.book1.id,
            'author': self.author2.id,
            'subject': 'Need clarification on royalty payout timeline',
            'description': 'My royalty for last month is showing pending. When will it disburse?'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ticket = Ticket.objects.get(id=response.data['id'])
        self.assertNotIn('ai_category', response.data)
        self.assertEqual(ticket.category, Ticket.Category.ACCOUNT)
        self.assertIsNone(ticket.ai_category)
        self.assertIsNone(ticket.ai_priority)
        self.assertIsNone(ticket.ai_suggested_response)
        self.assertEqual(ticket.author, self.author1)
        self.assertEqual(ticket.book, self.book1)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        self.assertEqual(response.data['ticket_id'], str(ticket.ticket_id))

        # Verify initial message thread created
        first_message = ticket.messages.first()
        self.assertIsNotNone(first_message)
        self.assertEqual(first_message.message, payload['description'])

        self.client.force_authenticate(user=self.admin_user)
        update_response = self.client.patch(
            reverse('ticket_detail', kwargs={'pk': ticket.pk}),
            {'category': 'PRINTING_QUALITY', 'priority': 'HIGH'},
            format='json',
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.category, 'PRINTING_QUALITY')
        self.assertEqual(ticket.priority, Ticket.Priority.HIGH)
        self.assertIsNone(ticket.ai_category)
        self.assertIsNone(ticket.ai_priority)

    def test_author_can_create_general_ticket_with_private_attachment(self):
        self.client.force_authenticate(user=self.author1)
        attachment = SimpleUploadedFile(
            'screenshot.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 12,
            content_type='image/png',
        )
        response = self.client.post(
            reverse('ticket_list_create'),
            {
                'subject': 'Account profile needs an update',
                'description': 'Please help me update my account details.',
                'attachment': attachment,
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ticket = Ticket.objects.get(pk=response.data['id'])
        self.assertIsNone(ticket.book)
        self.assertTrue(ticket.attachment.name.startswith('ticket-attachments/'))
        self.assertIn('/attachment/', response.data['attachment_url'])
        self.assertIsNone(ticket.ai_category)
        self.assertIsNone(ticket.ai_priority)
        self.assertIsNone(ticket.ai_suggested_response)
        self.addCleanup(ticket.attachment.delete, save=False)

        owner_response = self.client.get(
            reverse('ticket_attachment_download', kwargs={'pk': ticket.pk})
        )
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.author2)
        other_author_response = self.client.get(
            reverse('ticket_attachment_download', kwargs={'pk': ticket.pk})
        )
        self.assertEqual(other_author_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_cannot_create_ticket_for_another_authors_book(self):
        self.client.force_authenticate(user=self.author1)
        response = self.client.post(
            reverse('ticket_list_create'),
            {
                'book': self.book2.id,
                'subject': 'Question about my book',
                'description': 'I have a question about this book.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data)
        self.assertFalse(Ticket.objects.exists())

    def test_ticket_creation_requires_authentication(self):
        response = self.client.post(
            reverse('ticket_list_create'),
            {
                'subject': 'Support request',
                'description': 'Please help me with this issue.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Ticket.objects.exists())

    def test_author_can_read_admin_reply_and_send_a_reply(self):
        ticket = Ticket.objects.create(
            author=self.author1,
            subject='Book status question',
            description='Please update me about my book.',
        )
        admin_reply = TicketMessage.objects.create(
            ticket=ticket,
            sender=self.admin_user,
            message='Your book is currently in production.',
        )
        self.client.force_authenticate(user=self.author1)
        detail_response = self.client.get(
            reverse('ticket_detail', kwargs={'pk': ticket.pk})
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertNotIn('ai_suggested_response', detail_response.data)
        self.assertNotIn('ai_category', detail_response.data)
        self.assertEqual(detail_response.data['messages'][0]['id'], admin_reply.id)

        reply_response = self.client.post(
            reverse('ticket_message_create', kwargs={'pk': ticket.pk}),
            {
                'message': 'Thank you. Please let me know when it is complete.',
                'is_internal_note': True,
            },
            format='json',
        )
        self.assertEqual(reply_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(reply_response.data['is_internal_note'])

    @patch(
        'apps.support.views.generate_ticket_response_draft',
        return_value='Please tell us more about the issue.',
    )
    def test_only_admin_can_request_contextual_ai_response_drafts(self, generate_draft):
        ticket = Ticket.objects.create(
            author=self.author1,
            book=self.book1,
            subject='Book printing issue',
            description='Some pages are missing.',
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            reverse('ticket_ai_draft', kwargs={'pk': ticket.pk}),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['draft'], 'Please tell us more about the issue.')
        generate_draft.assert_called_once()

        self.client.force_authenticate(user=self.author1)
        author_response = self.client.post(
            reverse('ticket_ai_draft', kwargs={'pk': ticket.pk}),
            format='json',
        )
        self.assertEqual(author_response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.support.views.generate_ticket_response_draft', return_value=None)
    def test_manual_admin_reply_works_when_ai_is_unavailable(self, generate_draft):
        ticket = Ticket.objects.create(
            author=self.author1,
            subject='Account support',
            description='I need help with my account.',
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            reverse('ticket_message_create', kwargs={'pk': ticket.pk}),
            {'message': 'We can help with that.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'We can help with that.')
        generate_draft.assert_not_called()

    @patch('apps.support.views.broadcast_ticket_message', return_value=False)
    def test_reply_is_saved_when_live_delivery_is_unavailable(self, broadcast_message):
        ticket = Ticket.objects.create(
            author=self.author1,
            subject='Account support',
            description='I need help with my account.',
        )
        self.client.force_authenticate(user=self.author1)
        response = self.client.post(
            reverse('ticket_message_create', kwargs={'pk': ticket.pk}),
            {'message': 'I am following up on my account issue.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('delivery_warning', response.data)
        self.assertTrue(
            TicketMessage.objects.filter(
                ticket=ticket,
                message='I am following up on my account issue.',
            ).exists()
        )
        broadcast_message.assert_called_once()

    def test_invalid_attachment_type_is_rejected(self):
        self.client.force_authenticate(user=self.author1)
        upload = SimpleUploadedFile(
            'payload.exe',
            b'not an approved file type',
            content_type='application/octet-stream',
        )
        response = self.client.post(
            reverse('ticket_list_create'),
            {
                'subject': 'Support request',
                'description': 'Please review this supporting document.',
                'attachment': upload,
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('attachment', response.data)
        self.assertFalse(Ticket.objects.exists())

    def test_author_cannot_see_admin_internal_notes(self):
        # Create ticket for Author 1
        ticket = Ticket.objects.create(
            author=self.author1,
            subject='Cover design revision',
            description='I want to change the typography on cover page.'
        )

        # Admin adds an internal note
        TicketMessage.objects.create(
            ticket=ticket,
            sender=self.admin_user,
            message='Designer team is on holiday until Monday. Keep author on hold.',
            is_internal_note=True
        )

        # Author fetches ticket details
        self.client.force_authenticate(user=self.author1)
        url = reverse('ticket_detail', kwargs={'pk': ticket.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert internal notes are stripped out from messages
        messages = response.data.get('messages', [])
        for msg in messages:
            self.assertFalse(msg['is_internal_note'])