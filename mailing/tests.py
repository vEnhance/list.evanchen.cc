import pytest
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.urls import reverse

from .models import SubscriberEmail


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="pw"
    )


@pytest.fixture
def subscriber(db):
    return SubscriberEmail.objects.create(
        email="test@example.com",
        subscribed_blog=True,
        subscribed_wall=False,
    )


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


# --- index ---


def test_index(client, db):
    resp = client.get(reverse("index"))
    assert resp.status_code == 200


# --- edit_by_token ---


def test_edit_by_token_get_valid(client, subscriber):
    resp = client.get(reverse("edit_by_token", args=[subscriber.token]))
    assert resp.status_code == 200
    assert "form" in resp.context


def test_edit_by_token_get_bad_token(client, db):
    resp = client.get(reverse("edit_by_token", args=["x" * 24]))
    assert resp.status_code == 200
    assert "bad_token" in resp.templates[0].name


def test_edit_by_token_post_saves(client, subscriber):
    resp = client.post(
        reverse("edit_by_token", args=[subscriber.token]),
        {"subscribed_blog": False, "subscribed_wall": True},
    )
    assert resp.status_code == 200
    assert "edit_done" in resp.templates[0].name
    subscriber.refresh_from_db()
    assert subscriber.subscribed_blog is False
    assert subscriber.subscribed_wall is True


def test_edit_by_token_post_bad_token(client, db):
    resp = client.post(reverse("edit_by_token", args=["x" * 24]))
    assert resp.status_code == 200
    assert "bad_token" in resp.templates[0].name


# --- remove/<token>/ redirect ---


def test_remove_token_redirects(client, subscriber):
    resp = client.get(f"/remove/{subscriber.token}/")
    assert resp.status_code == 302
    assert resp["Location"] == reverse("edit_by_token", args=[subscriber.token])


# --- oauth_edit ---


def test_oauth_edit_requires_login(client, db):
    resp = client.get(reverse("oauth_edit"))
    assert resp.status_code == 302


def test_oauth_edit_get_existing(auth_client, user):
    SubscriberEmail.objects.create(
        email=user.email, subscribed_blog=True, subscribed_wall=False
    )
    resp = auth_client.get(reverse("oauth_edit"))
    assert resp.status_code == 200
    assert "form" in resp.context


def test_oauth_edit_get_creates_record(auth_client, user, db):
    resp = auth_client.get(reverse("oauth_edit"))
    assert resp.status_code == 200
    assert SubscriberEmail.objects.filter(email=user.email).exists()


def test_oauth_edit_get_preselects_blog_for_never_edited(auth_client, user, db):
    resp = auth_client.get(reverse("oauth_edit"))
    assert resp.context["form"]["subscribed_blog"].value() is True


def test_oauth_edit_get_no_preselect_after_save(auth_client, user):
    SubscriberEmail.objects.create(
        email=user.email, subscribed_blog=False, is_new=False
    )
    resp = auth_client.get(reverse("oauth_edit"))
    assert resp.context["form"]["subscribed_blog"].value() is False


def test_oauth_edit_post_saves(auth_client, user):
    SubscriberEmail.objects.create(email=user.email)
    resp = auth_client.post(
        reverse("oauth_edit"),
        {"subscribed_blog": False, "subscribed_wall": True},
    )
    assert resp.status_code == 200
    assert "edit_done" in resp.templates[0].name
    obj = SubscriberEmail.objects.get(email=user.email)
    assert obj.subscribed_blog is False
    assert obj.subscribed_wall is True


def test_oauth_edit_post_sets_google_authenticated(auth_client, user):
    SubscriberEmail.objects.create(email=user.email, google_authenticated=False)
    auth_client.post(
        reverse("oauth_edit"),
        {"subscribed_blog": True, "subscribed_wall": False},
    )
    obj = SubscriberEmail.objects.get(email=user.email)
    assert obj.google_authenticated is True


# --- subscriber_list_blog API ---


_TOKEN = "testtoken"


@pytest.fixture
def token_hash(settings):
    h = make_password(_TOKEN)
    settings.SUBSCRIBER_LIST_TOKEN_HASH = h
    return h


def test_subscriber_list_blog_no_auth(client, db, token_hash):
    resp = client.get(reverse("subscriber_list_blog"))
    assert resp.status_code == 401


def test_subscriber_list_blog_wrong_token(client, db, token_hash):
    resp = client.get(
        reverse("subscriber_list_blog"),
        HTTP_AUTHORIZATION="Bearer wrongtoken",
    )
    assert resp.status_code == 403


def test_subscriber_list_blog_returns_blog_only(client, db, token_hash):
    SubscriberEmail.objects.create(
        email="blog@example.com", subscribed_blog=True, subscribed_wall=False
    )
    SubscriberEmail.objects.create(
        email="wall@example.com", subscribed_blog=False, subscribed_wall=True
    )
    SubscriberEmail.objects.create(
        email="none@example.com", subscribed_blog=False, subscribed_wall=False
    )
    resp = client.get(
        reverse("subscriber_list_blog"),
        HTTP_AUTHORIZATION=f"Bearer {_TOKEN}",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "timestamp" in data
    subscribers = data["subscribers"]
    assert len(subscribers) == 1
    assert subscribers[0]["email"] == "blog@example.com"
    assert len(subscribers[0]["token"]) == 24


def test_subscriber_list_blog_post_not_allowed(client, db, token_hash):
    resp = client.post(
        reverse("subscriber_list_blog"),
        HTTP_AUTHORIZATION=f"Bearer {_TOKEN}",
    )
    assert resp.status_code == 405


# --- subscriber_list_wall API ---


def test_subscriber_list_wall_no_auth(client, db, token_hash):
    resp = client.get(reverse("subscriber_list_wall"))
    assert resp.status_code == 401


def test_subscriber_list_wall_wrong_token(client, db, token_hash):
    resp = client.get(
        reverse("subscriber_list_wall"),
        HTTP_AUTHORIZATION="Bearer wrongtoken",
    )
    assert resp.status_code == 403


def test_subscriber_list_wall_returns_wall_only(client, db, token_hash):
    SubscriberEmail.objects.create(
        email="blog@example.com", subscribed_blog=True, subscribed_wall=False
    )
    SubscriberEmail.objects.create(
        email="wall@example.com", subscribed_blog=False, subscribed_wall=True
    )
    SubscriberEmail.objects.create(
        email="none@example.com", subscribed_blog=False, subscribed_wall=False
    )
    resp = client.get(
        reverse("subscriber_list_wall"),
        HTTP_AUTHORIZATION=f"Bearer {_TOKEN}",
    )
    assert resp.status_code == 200
    data = resp.json()
    subscribers = data["subscribers"]
    assert len(subscribers) == 1
    assert subscribers[0]["email"] == "wall@example.com"


def test_subscriber_list_wall_post_not_allowed(client, db, token_hash):
    resp = client.post(
        reverse("subscriber_list_wall"),
        HTTP_AUTHORIZATION=f"Bearer {_TOKEN}",
    )
    assert resp.status_code == 405


# --- model ---


def test_token_generated_automatically(db):
    obj = SubscriberEmail.objects.create(email="auto@example.com")
    assert len(obj.token) == 24
    assert obj.token.isalnum()


def test_tokens_are_unique(db):
    a = SubscriberEmail.objects.create(email="a@example.com")
    b = SubscriberEmail.objects.create(email="b@example.com")
    assert a.token != b.token
