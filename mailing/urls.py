from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("edit/<str:token>/", views.edit_by_token, name="edit_by_token"),
    path(
        "remove/<str:token>/",
        RedirectView.as_view(pattern_name="edit_by_token"),
    ),
    path("oauth/edit/", views.oauth_edit, name="oauth_edit"),
    path(
        "api/subscribers/blog/", views.subscriber_list_blog, name="subscriber_list_blog"
    ),
    path(
        "api/subscribers/wall/", views.subscriber_list_wall, name="subscriber_list_wall"
    ),
    path("hohoho/", views.hohoho),
]
