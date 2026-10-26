from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'status', 'mrp', 'sales_count', 'royalty_pending')
    list_filter = ('status', 'genre')
    search_fields = ('title', 'isbn', 'author__username')