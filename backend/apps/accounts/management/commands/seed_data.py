from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.books.models import Book
from apps.support.models import Ticket, TicketMessage
from decimal import Decimal
import datetime

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial sample data for BookLeaf AuthorConnect portal"

    def handle(self, *args, **options):
        self.stdout.write("Seeding AuthorConnect database...")

        # 1. Create Admin User
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@bookleaf.com",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("AdminPass123!")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / AdminPass123!"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Create Sample Authors
        authors_data = [
            {"username": "rohit_author", "email": "rohit@example.com", "phone": "+91-9876543210"},
            {"username": "priya_author", "email": "priya@example.com", "phone": "+91-9123456789"},
        ]

        created_authors = []
        for a_data in authors_data:
            author, created = User.objects.get_or_create(
                username=a_data["username"],
                defaults={
                    "email": a_data["email"],
                    "role": User.Role.AUTHOR,
                    "phone_number": a_data["phone"],
                    "is_staff": False,
                }
            )
            if created:
                author.set_password("AuthorPass123!")
                author.save()
                self.stdout.write(self.style.SUCCESS(f"Created author: {author.username} / AuthorPass123!"))
            created_authors.append(author)

        author_1 = created_authors[0]
        author_2 = created_authors[1]

        # 3. Create Books
        books_data = [
            {
                "author": author_1,
                "title": "Echoes of the Silent Valley",
                "isbn": "978-81-923456-0-1",
                "genre": "Fiction / Mystery",
                "publication_date": datetime.date(2025, 4, 15),
                "status": Book.Status.PUBLISHED,
                "mrp": Decimal("499.00"),
                "sales_count": 320,
                "royalty_earned": Decimal("23952.00"),
                "royalty_paid": Decimal("18000.00"),
                "royalty_pending": Decimal("5952.00"),
            },
            {
                "author": author_1,
                "title": "Whispers in the Rain",
                "isbn": "978-81-923456-1-8",
                "genre": "Poetry",
                "publication_date": datetime.date(2025, 9, 1),
                "status": Book.Status.PUBLISHED,
                "mrp": Decimal("299.00"),
                "sales_count": 140,
                "royalty_earned": Decimal("6279.00"),
                "royalty_paid": Decimal("6279.00"),
                "royalty_pending": Decimal("0.00"),
            },
            {
                "author": author_2,
                "title": "The Tech Innovator's Blueprint",
                "isbn": "978-81-923456-2-5",
                "genre": "Technology / Business",
                "publication_date": datetime.date(2026, 1, 10),
                "status": Book.Status.PUBLISHED,
                "mrp": Decimal("799.00"),
                "sales_count": 510,
                "royalty_earned": Decimal("61123.50"),
                "royalty_paid": Decimal("45000.00"),
                "royalty_pending": Decimal("16123.50"),
            },
        ]

        created_books = []
        for b_data in books_data:
            book, created = Book.objects.get_or_create(
                isbn=b_data["isbn"],
                defaults=b_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created book: {book.title}"))
            created_books.append(book)

        # 4. Create Sample Support Tickets
        ticket_1, created = Ticket.objects.get_or_create(
            subject="October royalty payout status inquiry",
            author=author_1,
            defaults={
                "book": created_books[0],
                "description": "Hi BookLeaf team, I saw my pending royalty is Rs 5952. When can I expect this disbursed to my account?",
                "category": Ticket.Category.ROYALTY,
                "priority": Ticket.Priority.MEDIUM,
                "status": Ticket.Status.OPEN,
                "assigned_to": admin_user,
                "ai_category": "ROYALTY",
                "ai_priority": "MEDIUM",
                "ai_suggested_response": "Hello Rohit, October royalties are processed between the 1st and 7th of every following month. Your pending amount of Rs 5952 is queued for transfer.",
            }
        )

        if created:
            TicketMessage.objects.create(
                ticket=ticket_1,
                sender=author_1,
                message=ticket_1.description
            )
            self.stdout.write(self.style.SUCCESS("Created sample ticket for Rohit"))

        self.stdout.write(self.style.SUCCESS("\nDatabase successfully seeded with idempotent data!"))