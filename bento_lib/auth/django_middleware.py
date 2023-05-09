from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.http import HttpRequest
from .middleware.base import BaseAuthMiddleware


def extract_middleware_arguments() -> tuple:
    middleware_settings = getattr(settings, "BENTO_AUTHZ_MIDDLEWARE_CONFIG", {})
    return (
        middleware_settings["AUTHZ_SERVICE_URL"],
        middleware_settings["OPENID_CONFIG_URL"],
        middleware_settings["OPENID_AUD"],
        middleware_settings.get("DISALLOWED_ALGORITHMS", frozenset({})),
        middleware_settings.get("DRS_COMPAT", False),
        middleware_settings.get("SR_COMPAT", False),
        settings.DEBUG,
        middleware_settings.get("LOGGER"),
    )


class AsyncDjangoMiddleware(BaseAuthMiddleware):
    def __init__(self, get_response):
        # TODO: extract settings from Django settings

        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

        super().__init__(*extract_middleware_arguments())

    async def __call__(self, request: HttpRequest):
        request.bento_determined_authz = False  # Just cram a new property in there... no state object
        # TODO: impl
        pass


class SyncDjangoMiddleware(BaseAuthMiddleware):
    def __init__(self):
        # TODO: extract settings from Django settings
        super().__init__(*extract_middleware_arguments())

    def __call__(self, request: HttpRequest):
        request.bento_determined_authz = False  # Just cram a new property in there... no state object
        # TODO: impl
        pass
