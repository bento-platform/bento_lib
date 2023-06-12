from django.urls import path

from . import views

urlpatterns = [
    path("post-private", views.auth_post_private, name="post-private"),
    path("post-private-no-flag", views.auth_post_private_no_flag, name="post-private-no-flag"),
    path("post-private-no-token", views.auth_post_private_no_token, name="post-private-no-token"),
    path("post-missing-authz", views.auth_post_missing_authz, name="post-missing-authz"),
    path("post-exc", views.auth_post_exception, name="post-exc"),
]
