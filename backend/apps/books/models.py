from django.db import models
from django.conf import settings


class Book(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        PUBLISHED = 'PUBLISHED', 'Published'
        OUT_OF_PRINT = 'OUT_OF_PRINT', 'Out of Print'

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='books'
    )
    title = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True)
    publication_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED
    )
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sales_count = models.PositiveIntegerField(default=0)
    royalty_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    royalty_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    royalty_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.author.username}"