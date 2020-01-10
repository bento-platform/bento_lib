from django.contrib.auth.backends import RemoteUserBackend
from .roles import *


__all__ = ["CHORDRemoteUserBackend"]


class CHORDRemoteUserBackend(RemoteUserBackend):
    header = "HTTP_X_USER"

    def configure_user(self, request, user):
        is_owner = request.META.get("HTTP_X_USER_ROLE", ROLE_USER) == ROLE_OWNER
        user.is_staff = is_owner
        user.is_superuser = is_owner
        return user
