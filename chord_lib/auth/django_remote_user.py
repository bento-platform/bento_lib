from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from rest_framework.authentication import RemoteUserAuthentication

from .roles import *


__all__ = [
    "CHORDRemoteUserAuthentication",
    "CHORDRemoteUserBackend",
    "CHORDRemoteUserMiddleware",
]


USER_HEADER = "HTTP_X_USER"


class CHORDRemoteUserAuthentication(RemoteUserAuthentication):
    header = USER_HEADER


class CHORDRemoteUserMiddleware(RemoteUserMiddleware):
    header = USER_HEADER


class CHORDRemoteUserBackend(RemoteUserBackend):
    def configure_user(self, request, user):
        is_owner = request.META.get("HTTP_X_USER_ROLE", ROLE_USER) == ROLE_OWNER
        user.is_staff = is_owner
        user.is_superuser = is_owner
        user.save()
        return user
