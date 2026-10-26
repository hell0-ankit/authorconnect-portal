from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path("books/", include("apps.books.urls")),
    path("support/", include("apps.support.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
