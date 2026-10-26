from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Book
from .serializers import BookListSerializer, BookDetailSerializer
from apps.core.pagination import StandardResultsSetPagination


class BookListView(generics.ListAPIView):
    """
    List books endpoint:
    - Admin: can see all books, with optional filter by ?author_id=<id>
    - Author: strictly scoped to own books.
    """
    serializer_class = BookListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            queryset = Book.objects.select_related('author').all()
            author_id = self.request.query_params.get('author_id')
            if author_id:
                queryset = queryset.filter(author_id=author_id)
            return queryset
        return Book.objects.filter(author=user)


class BookDetailView(generics.RetrieveAPIView):
    """
    Retrieve single book details:
    - Admin: can inspect any book.
    - Author: ownership enforced, returns 404 if accessed by unauthorized author.
    """
    serializer_class = BookDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Book.objects.select_related('author').all()
        return Book.objects.filter(author=user)