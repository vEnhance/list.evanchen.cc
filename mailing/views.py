from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now

from .forms import EditSubscriptionForm
from .models import SubscriberEmail


def index(request):
    return render(request, "mailing/index.html", {"page_title": "Evan's mailing list"})


def edit_by_token(request, token):
    try:
        obj = SubscriberEmail.objects.get(token=token)
    except SubscriberEmail.DoesNotExist:
        return render(request, "mailing/bad_token.html", {"page_title": "Link invalid"})
    if request.method == "POST":
        form = EditSubscriptionForm(request.POST, instance=obj)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.is_new = False
            instance.save()
            return render(
                request,
                "mailing/edit_done.html",
                {
                    "page_title": "Form saved",
                    "email": obj.email,
                    "form": EditSubscriptionForm(instance=obj),
                    "back_url": reverse("edit_by_token", args=[token]),
                },
            )
    else:
        form = EditSubscriptionForm(instance=obj)
    page_title = "Add a new email" if obj.is_new else "Edit email settings"
    return render(
        request,
        "mailing/edit_form.html",
        {
            "page_title": page_title,
            "form": form,
            "email": obj.email,
            "is_new": obj.is_new,
        },
    )


@login_required
def oauth_edit(request):
    email = request.user.email
    obj, _ = SubscriberEmail.objects.get_or_create(email=email)
    if not obj.google_authenticated:
        obj.google_authenticated = True
        obj.save()
    if request.method == "POST":
        form = EditSubscriptionForm(request.POST, instance=obj)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.is_new = False
            if not instance.name:
                instance.name = request.user.get_full_name()
            instance.save()
            return render(
                request,
                "mailing/edit_done.html",
                {
                    "page_title": "Form saved",
                    "email": email,
                    "form": EditSubscriptionForm(instance=obj),
                    "back_url": reverse("oauth_edit"),
                },
            )
    else:
        if obj.is_new:
            obj.subscribed_blog = (
                True  # default display before first save; not written to DB
            )
        form = EditSubscriptionForm(instance=obj)
    return render(
        request,
        "mailing/edit_form.html",
        {
            "page_title": "Add a new email" if obj.is_new else "Edit email settings",
            "form": form,
            "email": email,
            "is_new": obj.is_new,
        },
    )


def hohoho(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=403)
    email = request.user.email
    if not SubscriberEmail.objects.filter(email=email, subscribed_blog=True).exists():
        return HttpResponse(status=403)
    return HttpResponse(f"Merry Christmas! For otters: {settings.SANTA_CODE}")


def _subscriber_list_view(request: HttpRequest, filter_kwargs: dict) -> JsonResponse:
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    expected_hash = settings.SUBSCRIBER_LIST_TOKEN_HASH
    if not expected_hash:
        return JsonResponse({"error": "API not configured"}, status=503)
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    provided_token = auth_header[len("Bearer ") :]
    if not check_password(provided_token, expected_hash):
        return JsonResponse({"error": "Forbidden"}, status=403)
    subscribers = list(
        SubscriberEmail.objects.filter(**filter_kwargs).values(
            "email", "token", "name", "custom_greeting"
        )
    )
    return JsonResponse({"timestamp": now().isoformat(), "subscribers": subscribers})


def subscriber_list_blog(request: HttpRequest) -> JsonResponse:
    return _subscriber_list_view(request, {"subscribed_blog": True})


def subscriber_list_wall(request: HttpRequest) -> JsonResponse:
    return _subscriber_list_view(request, {"subscribed_wall": True})
