from typing import ClassVar

from django import forms
from django.utils.safestring import mark_safe

from .models import SubscriberEmail


class EditSubscriptionForm(forms.ModelForm):
    class Meta:
        model = SubscriberEmail
        fields = ("subscribed_blog", "subscribed_wall")
        labels: ClassVar[dict[str, str]] = {
            "subscribed_blog": mark_safe(
                '<a href="https://blog.evanchen.cc">blog.evanchen.cc</a>'
            ),
            "subscribed_wall": mark_safe(
                '<a href="https://wall.evanchen.cc">wall.evanchen.cc</a>'
            ),
        }
        help_texts: ClassVar[dict[str, str]] = {
            "subscribed_blog": "Long posts every 1-3 months. Probably what you want.",
            "subscribed_wall": "Daily shower thoughts. Super noisy. Use with care.",
        }
