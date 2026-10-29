from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.books.models import Book
from apps.support.models import Ticket, TicketMessage
from decimal import Decimal
import datetime
import re

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial sample data for BookLeaf AuthorConnect portal"

    def handle(self, *args, **options):
        self.stdout.write("Seeding AuthorConnect database...")

        # 1. Create Admin User
        admin_user, created = User.objects.update_or_create(
            username="admin",
            defaults={
                "email": "admin@bookleaf.com",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("AdminPass123!")
        admin_user.save(update_fields=["password"])

        if created:
            self.stdout.write(
                self.style.SUCCESS("Created admin user: admin / AdminPass123!")
            )
        else:
            self.stdout.write("Updated existing admin user.")

        # 2. Authors: use only existing User fields
        authors_data = [
            {"name": "Priya Sharma", "email": "priya.sharma@email.com", "phone": "+91-98765-43210"},
            {"name": "Rohit Kapoor", "email": "rohit.kapoor@email.com", "phone": "+91-87654-32109"},
            {"name": "Ananya Reddy", "email": "ananya.reddy@email.com", "phone": "+91-76543-21098"},
            {"name": "Vikram Joshi", "email": "vikram.joshi@email.com", "phone": "+91-65432-10987"},
            {"name": "Meera Nair", "email": "meera.nair@email.com", "phone": "+91-54321-09876"},
            {"name": "Arjun Malhotra", "email": "arjun.malhotra@email.com", "phone": "+91-43210-98765"},
            {"name": "Sneha Kulkarni", "email": "sneha.kulkarni@email.com", "phone": "+91-32109-87654"},
            {"name": "Farhan Sheikh", "email": "farhan.sheikh@email.com", "phone": "+91-21098-76543"},
            {"name": "Kavita Deshmukh", "email": "kavita.deshmukh@email.com", "phone": "+91-10987-65432"},
            {"name": "Diya Chatterjee", "email": "diya.chatterjee@email.com", "phone": "+91-09876-54321"},
        ]

        authors = {}

        for data in authors_data:
            username = re.sub(r"[^a-z0-9]+", "_", data["name"].lower()).strip("_")

            author, created = User.objects.update_or_create(
                username=username,
                defaults={
                    "email": data["email"],
                    "role": User.Role.AUTHOR,
                    "phone_number": data["phone"],
                    "is_staff": False,
                },
            )
            author.set_password("AuthorPass123!")
            author.save(update_fields=["password"])

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created author: {username}")
                )
            else:
                self.stdout.write(f"Updated existing author: {username}")

            authors[data["name"]] = author

        # 3. Book data: only fields already used by the existing seed
        books_data = [
            {
                "author_name": "Priya Sharma",
                "title": "Whispers of the Ganges",
                "isbn": "9789350000007",
                "genre": "Literary Fiction",
                "publication_date": datetime.date(2023, 6, 20),
                "mrp": Decimal("399.00"),
                "sales_count": 342,
                "royalty_earned": Decimal("11970.00"),
                "royalty_paid": Decimal("8400.00"),
                "royalty_pending": Decimal("3570.00"),
                "is_published": True,
            },
            {
                "author_name": "Priya Sharma",
                "title": "The Saffron Diaries",
                "isbn": "9789350000014",
                "genre": "Non-Fiction / Memoir",
                "publication_date": datetime.date(2024, 1, 10),
                "mrp": Decimal("450.00"),
                "sales_count": 189,
                "royalty_earned": Decimal("7938.00"),
                "royalty_paid": Decimal("7938.00"),
                "royalty_pending": Decimal("0.00"),
                "is_published": True,
            },
            {
                "author_name": "Rohit Kapoor",
                "title": "Code & Karma",
                "isbn": "9789350000021",
                "genre": "Self-Help / Technology",
                "publication_date": datetime.date(2023, 2, 14),
                "mrp": Decimal("350.00"),
                "sales_count": 876,
                "royalty_earned": Decimal("26280.00"),
                "royalty_paid": Decimal("21000.00"),
                "royalty_pending": Decimal("5280.00"),
                "is_published": True,
            },
            {
                "author_name": "Rohit Kapoor",
                "title": "Startup Sutra",
                "isbn": "9789350000038",
                "genre": "Business / Entrepreneurship",
                "publication_date": datetime.date(2024, 5, 22),
                "mrp": Decimal("499.00"),
                "sales_count": 1203,
                "royalty_earned": Decimal("57744.00"),
                "royalty_paid": Decimal("50000.00"),
                "royalty_pending": Decimal("7744.00"),
                "is_published": True,
            },
            {
                "author_name": "Ananya Reddy",
                "title": "Between Two Temples",
                "isbn": "9789350000045",
                "genre": "Historical Fiction",
                "publication_date": datetime.date(2024, 7, 5),
                "mrp": Decimal("425.00"),
                "sales_count": 67,
                "royalty_earned": Decimal("2546.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("2546.00"),
                "is_published": True,
            },
            {
                "author_name": "Vikram Joshi",
                "title": "Debugging Life",
                "isbn": "9789350000052",
                "genre": "Self-Help",
                "publication_date": datetime.date(2023, 11, 30),
                "mrp": Decimal("299.00"),
                "sales_count": 534,
                "royalty_earned": Decimal("13350.00"),
                "royalty_paid": Decimal("10000.00"),
                "royalty_pending": Decimal("3350.00"),
                "is_published": True,
            },
            {
                "author_name": "Vikram Joshi",
                "title": "The Last Monsoon",
                "isbn": "9789350000069",
                "genre": "Poetry",
                "publication_date": datetime.date(2024, 8, 15),
                "mrp": Decimal("199.00"),
                "sales_count": 123,
                "royalty_earned": Decimal("1845.00"),
                "royalty_paid": Decimal("1845.00"),
                "royalty_pending": Decimal("0.00"),
                "is_published": True,
            },
            {
                "author_name": "Meera Nair",
                "title": "Cardamom & Chaos",
                "isbn": "9789350000076",
                "genre": "Contemporary Fiction",
                "publication_date": datetime.date(2023, 4, 18),
                "mrp": Decimal("375.00"),
                "sales_count": 445,
                "royalty_earned": Decimal("14240.00"),
                "royalty_paid": Decimal("14240.00"),
                "royalty_pending": Decimal("0.00"),
                "is_published": True,
            },
            {
                "author_name": "Meera Nair",
                "title": "Letters from Lakshadweep",
                "isbn": "9789350000083",
                "genre": "Travel / Non-Fiction",
                "publication_date": datetime.date(2024, 3, 1),
                "mrp": Decimal("550.00"),
                "sales_count": 201,
                "royalty_earned": Decimal("11055.00"),
                "royalty_paid": Decimal("8000.00"),
                "royalty_pending": Decimal("3055.00"),
                "is_published": True,
            },
            {
                "author_name": "Arjun Malhotra",
                "title": "Turban Tales",
                "isbn": "9789350000090",
                "genre": "Humor / Essays",
                "publication_date": datetime.date(2024, 9, 10),
                "mrp": Decimal("325.00"),
                "sales_count": 88,
                "royalty_earned": Decimal("2464.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("2464.00"),
                "is_published": True,
            },
            {
                "author_name": "Sneha Kulkarni",
                "title": "The Algorithm of Love",
                "isbn": "9789350000106",
                "genre": "Romance",
                "publication_date": datetime.date(2022, 12, 25),
                "mrp": Decimal("299.00"),
                "sales_count": 1567,
                "royalty_earned": Decimal("39175.00"),
                "royalty_paid": Decimal("35000.00"),
                "royalty_pending": Decimal("4175.00"),
                "is_published": True,
            },
            {
                "author_name": "Sneha Kulkarni",
                "title": "Ctrl+Alt+Delete My Ex",
                "isbn": "9789350000113",
                "genre": "Romance / Humor",
                "publication_date": datetime.date(2024, 2, 14),
                "mrp": Decimal("350.00"),
                "sales_count": 723,
                "royalty_earned": Decimal("21690.00"),
                "royalty_paid": Decimal("18000.00"),
                "royalty_pending": Decimal("3690.00"),
                "is_published": True,
            },
            {
                "author_name": "Sneha Kulkarni",
                "title": "Midnight in Mysore",
                "isbn": "9789350000120",
                "genre": "Thriller",
                "publication_date": None,
                "mrp": Decimal("0.00"),
                "sales_count": 0,
                "royalty_earned": Decimal("0.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("0.00"),
                "is_published": False,
            },
            {
                "author_name": "Farhan Sheikh",
                "title": "Ghazal of the Forgotten",
                "isbn": "9789350000137",
                "genre": "Poetry / Urdu Literature",
                "publication_date": datetime.date(2024, 1, 26),
                "mrp": Decimal("250.00"),
                "sales_count": 156,
                "royalty_earned": Decimal("3120.00"),
                "royalty_paid": Decimal("3120.00"),
                "royalty_pending": Decimal("0.00"),
                "is_published": True,
            },
            {
                "author_name": "Kavita Deshmukh",
                "title": "Raising Roots",
                "isbn": "9789350000144",
                "genre": "Parenting / Non-Fiction",
                "publication_date": None,
                "mrp": Decimal("0.00"),
                "sales_count": 0,
                "royalty_earned": Decimal("0.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("0.00"),
                "is_published": False,
            },
            {
                "author_name": "Kavita Deshmukh",
                "title": "The Nagpur Notebooks",
                "isbn": "9789350000151",
                "genre": "Essays / Memoir",
                "publication_date": datetime.date(2024, 11, 5),
                "mrp": Decimal("299.00"),
                "sales_count": 34,
                "royalty_earned": Decimal("850.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("850.00"),
                "is_published": True,
            },
            {
                "author_name": "Diya Chatterjee",
                "title": "Durga’s Daughters",
                "isbn": "9789350000168",
                "genre": "Literary Fiction",
                "publication_date": datetime.date(2023, 10, 15),
                "mrp": Decimal("475.00"),
                "sales_count": 612,
                "royalty_earned": Decimal("27540.00"),
                "royalty_paid": Decimal("25000.00"),
                "royalty_pending": Decimal("2540.00"),
                "is_published": True,
            },
            {
                "author_name": "Diya Chatterjee",
                "title": "Howrah Nights",
                "isbn": "9789350000175",
                "genre": "Crime / Thriller",
                "publication_date": datetime.date(2025, 1, 20),
                "mrp": Decimal("399.00"),
                "sales_count": 45,
                "royalty_earned": Decimal("1575.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("1575.00"),
                "is_published": True,
            },
        ]

        # Resolve a suitable non-published status from existing model choices.
        non_published_status = None
        for value, label in Book.Status.choices:
            if value != Book.Status.PUBLISHED and any(
                word in f"{value} {label}".lower()
                for word in ("production", "draft", "pending", "review")
            ):
                non_published_status = value
                break

        created_books = {}

        for data in books_data:
            author = authors[data["author_name"]]

            status = (
                Book.Status.PUBLISHED
                if data["is_published"]
                else non_published_status
            )

            if status is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping '{data['title']}': no non-published "
                        "status is defined in Book.Status."
                    )
                )
                continue

            book_defaults = {
                "author": author,
                "title": data["title"],
                "genre": data["genre"],
                "publication_date": data["publication_date"],
                "status": status,
                "mrp": data["mrp"],
                "sales_count": data["sales_count"],
                "royalty_earned": data["royalty_earned"],
                "royalty_paid": data["royalty_paid"],
                "royalty_pending": data["royalty_pending"],
            }

            book, created = Book.objects.update_or_create(
                isbn=data["isbn"],
                defaults=book_defaults,
            )

            created_books[data["title"]] = book

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created book: {book.title}")
                )
            else:
                self.stdout.write(f"Updated existing book: {book.title}")

        # 4. Preserve sample Support Ticket logic for Rohit Kapoor
        author_1 = authors["Rohit Kapoor"]
        ticket_book = created_books.get("Code & Karma")

        if ticket_book:
            ticket_1, created = Ticket.objects.update_or_create(
                subject="October royalty payout status inquiry",
                author=author_1,
                defaults={
                    "book": ticket_book,
                    "description": (
                        "Hi BookLeaf team, I saw my pending royalty is "
                        "Rs 5280. When can I expect this disbursed "
                        "to my account?"
                    ),
                    "category": Ticket.Category.ROYALTY,
                    "priority": Ticket.Priority.MEDIUM,
                    "status": Ticket.Status.OPEN,
                    "assigned_to": admin_user,
                    "ai_category": "ROYALTY",
                    "ai_priority": "MEDIUM",
                    "ai_suggested_response": (
                        "Hello Rohit, we need to verify the relevant sales "
                        "period and payment status before confirming a "
                        "payment or resolution timeline."
                    ),
                },
            )

            seed_message = TicketMessage.objects.filter(
                ticket=ticket_1,
                sender=author_1,
                is_internal_note=False,
            ).order_by("created_at").first()

            if seed_message is None:
                TicketMessage.objects.create(
                    ticket=ticket_1,
                    sender=author_1,
                    message=ticket_1.description,
                )
            else:
                seed_message.message = ticket_1.description
                seed_message.save(update_fields=["message"])

            if created:
                self.stdout.write(
                    self.style.SUCCESS("Created sample ticket for Rohit")
                )
            else:
                self.stdout.write(
                    "Updated existing sample ticket for Rohit"
                )

        self.stdout.write(
            self.style.SUCCESS(
                "\nDatabase successfully seeded with idempotent data!"
            )
        )