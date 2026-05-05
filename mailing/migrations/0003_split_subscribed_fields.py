from django.db import migrations, models


def split_subscribed(apps, schema_editor):
    SubscriberEmail = apps.get_model("mailing", "SubscriberEmail")
    SubscriberEmail.objects.filter(subscribed=True).update(subscribed_blog=True)


def merge_subscribed(apps, schema_editor):
    SubscriberEmail = apps.get_model("mailing", "SubscriberEmail")
    SubscriberEmail.objects.filter(subscribed_blog=True).update(subscribed=True)
    SubscriberEmail.objects.filter(subscribed_blog=False).update(subscribed=None)


class Migration(migrations.Migration):
    dependencies = [
        ("mailing", "0002_subscriberemail_custom_greeting_subscriberemail_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriberemail",
            name="subscribed_blog",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="subscriberemail",
            name="subscribed_wall",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(split_subscribed, merge_subscribed),
        migrations.RemoveField(
            model_name="subscriberemail",
            name="subscribed",
        ),
    ]
