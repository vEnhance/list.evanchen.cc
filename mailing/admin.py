from django.contrib import admin

from .models import SubscriberEmail


@admin.register(SubscriberEmail)
class SubscriberEmailAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "is_new",
        "name",
        "subscribed_blog",
        "subscribed_wall",
        "custom_greeting",
        "created_at",
        "google_authenticated",
    )
    list_filter = (
        "is_new",
        "subscribed_blog",
        "subscribed_wall",
        "google_authenticated",
    )
    search_fields = ("email",)
    readonly_fields = ("token", "created_at", "updated_at")
