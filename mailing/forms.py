from django import forms

from .models import SubscriberEmail


class EditSubscriptionForm(forms.ModelForm):
    class Meta:
        model = SubscriberEmail
        fields = ["subscribed_blog", "subscribed_wall"]
        labels = {
            "subscribed_blog": "blog.evanchen.cc",
            "subscribed_wall": "wall.evanchen.cc",
        }
        help_texts = {
            "subscribed_blog": "Long posts every 1-3 months. Probably what you want.",
            "subscribed_wall": "Daily shower thoughts. Super noisy. Use with care.",
        }
