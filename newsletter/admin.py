from django.contrib import admin
from django.utils import timezone

from .models import NewsletterSubscriber, QuoteEmailConsent


class ConsentAdmin(admin.ModelAdmin):
    search_fields = ("email", "event_id")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(QuoteEmailConsent)
class QuoteEmailConsentAdmin(ConsentAdmin):
    list_display = ("email", "event_id", "accepted_at")
    readonly_fields = ("email", "event_id", "accepted_at", "consent_text")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ConsentAdmin):
    list_display = ("email", "accepted_at", "source", "unsubscribed_at")
    list_filter = ("source", "unsubscribed_at")
    readonly_fields = ("email", "accepted_at", "consent_text", "source", "event_id", "unsubscribed_at")
    actions = ("unsubscribe",)

    @admin.action(description="Désinscrire les contacts sélectionnés de la newsletter")
    def unsubscribe(self, request, queryset):
        queryset.filter(unsubscribed_at__isnull=True).update(unsubscribed_at=timezone.now())
