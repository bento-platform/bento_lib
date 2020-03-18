from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from rest_framework.authentication import RemoteUserAuthentication

from chord_lib.auth.headers import DJANGO_USER_HEADER, DJANGO_USER_ROLE_HEADER
from chord_lib.auth.roles import ROLE_OWNER, ROLE_USER


__all__ = [
    "CHORDRemoteUserAuthentication",
    "CHORDRemoteUserBackend",
    "CHORDRemoteUserMiddleware",
]


class CHORDRemoteUserAuthentication(RemoteUserAuthentication):
    header = DJANGO_USER_HEADER


class CHORDRemoteUserMiddleware(RemoteUserMiddleware):
    header = DJANGO_USER_HEADER


class CHORDRemoteUserBackend(RemoteUserBackend):
    # noinspection PyMethodMayBeStatic
    def configure_user(self, request, user):
        is_owner = request.META.get(DJANGO_USER_ROLE_HEADER, ROLE_USER) == ROLE_OWNER
        user.is_staff = is_owner
        user.is_superuser = is_owner
        user.save()
        return user
