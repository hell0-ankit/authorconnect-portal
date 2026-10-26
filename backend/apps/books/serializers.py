from rest_framework import serializers
from .models import Book
from apps.accounts.serializers import UserSerializer


class BookListSerializer(serializers.ModelSerializer):
    """
    Compact serializer for listing books in the author dashboard and support ticket dropdowns.
    """
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'author_name',
            'title',
            'isbn',
            'genre',
            'status',
            'publication_date',
            'sales_count',
            'royalty_pending',
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer exposing all sales, pricing, and royalty metrics.
    """
    author = UserSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'author',
            'title',
            'isbn',
            'genre',
            'publication_date',
            'status',
            'mrp',
            'sales_count',
            'royalty_earned',
            'royalty_paid',
            'royalty_pending',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'author',
            'sales_count',
            'royalty_earned',
            'royalty_paid',
            'royalty_pending',
            'created_at',
            'updated_at',
        ]