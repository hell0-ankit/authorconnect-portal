from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.books.models import Book
from apps.support.models import Ticket, TicketMessage

User = get_user_model()


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

    def test_admin_can_see_all_books(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('book_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        book_ids = [b['id'] for b in response.data['results']]
        self.assertIn(self.book1.id, book_ids)
        self.assertIn(self.book2.id, book_ids)

    def test_author_create_ticket_with_ai_fallback(self):
        self.client.force_authenticate(user=self.author1)
        url = reverse('ticket_list_create')
        payload = {
            'subject': 'Need clarification on royalty payout timeline',
            'description': 'My royalty for last month is showing pending. When will it disburse?'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ticket = Ticket.objects.get(id=response.data['id'])
        self.assertEqual(ticket.category, Ticket.Category.ROYALTY)
        self.assertEqual(ticket.author, self.author1)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

        # Verify initial message thread created
        first_message = ticket.messages.first()
        self.assertIsNotNone(first_message)
        self.assertEqual(first_message.message, payload['description'])

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