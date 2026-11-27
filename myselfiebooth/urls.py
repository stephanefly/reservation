from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from quote_control.history_api import auto_quote_history

urlpatterns = [
    path('api/v1/auto-quotes/history/', auto_quote_history, name='auto_quote_history'),
    path('', include('app.urls')),
    path('admin/', admin.site.urls),
]
if settings.NEWSLETTER_AVAILABLE:
    urlpatterns = [
        path('backend/newsletter/', include('newsletter.urls')),
        path('newsletter/', include('newsletter.public_urls')),
        *urlpatterns,
    ]
