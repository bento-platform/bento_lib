# !!! LEGACY FILE !!!

from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from rest_framework.authentication import RemoteUserAuthentication

from bento_lib.auth.headers import DJANGO_USER_HEADER, DJANGO_USER_ROLE_HEADER
from bento_lib.auth.roles import ROLE_OWNER, ROLE_USER


__all__ = [
    "BentoRemoteUserAuthentication",
    "BentoRemoteUserBackend",
    "BentoRemoteUserMiddleware",
]


class BentoRemoteUserAuthentication(RemoteUserAuthentication):
    header = DJANGO_USER_HEADER


class BentoRemoteUserMiddleware(RemoteUserMiddleware):
    header = DJANGO_USER_HEADER


class BentoRemoteUserBackend(RemoteUserBackend):
    # noinspection PyMethodMayBeStatic
    def configure_user(self, request, user):
        is_owner = request.META.get(DJANGO_USER_ROLE_HEADER, ROLE_USER) == ROLE_OWNER
        user.is_staff = is_owner
        user.is_superuser = is_owner
        user.save()
        return user
