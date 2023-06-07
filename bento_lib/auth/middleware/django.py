from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse
from typing import Awaitable, Callable

from bento_lib.responses.errors import http_error
from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.base import BaseAuthMiddleware

__all__ = [
    "DjangoAuthMiddleware",
]


class DjangoAuthMiddleware(BaseAuthMiddleware):
    async_capable = True
    sync_capable = True

    @staticmethod
    def extract_middleware_arguments() -> tuple:
        middleware_settings = getattr(settings, "BENTO_AUTHZ_MIDDLEWARE_CONFIG", {})
        return (
            middleware_settings["AUTHZ_SERVICE_URL"],
            middleware_settings.get("DRS_COMPAT", False),
            middleware_settings.get("SR_COMPAT", False),
            settings.DEBUG,
            middleware_settings.get("ENABLED", True),
            middleware_settings.get("LOGGER"),
        )

    def __init__(self, get_response):
        self.get_response: Callable[[HttpRequest], Awaitable[HttpResponse] | HttpResponse] = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

        super().__init__(*DjangoAuthMiddleware.extract_middleware_arguments())

    def get_authz_header_value(self, request: HttpRequest) -> str | None:
        return request.headers.get("Authorization")

    @staticmethod
    def mark_authz_done(request: HttpRequest):
        request.bento_determined_authz = True

    async def __call__(self, request: HttpRequest):
        if not self.enabled:
            return await self.get_response(request)

        request.bento_determined_authz = False

        try:
            response = await self.get_response(request)  # We've just crammed a new property in there... no state object
            if not request.bento_determined_authz:
                # Next in response chain didn't properly think about auth; return 403
                return JsonResponse(
                    http_error(403, "Forbidden", drs_compat=self._drs_compat, sr_compat=self._sr_compat),
                    status=403)

        except BentoAuthException as e:
            self.mark_authz_done(request)
            return JsonResponse(
                http_error(e.status_code, e.message, drs_compat=self._drs_compat, sr_compat=self._sr_compat),
                status_code=e.status_code)

        # Otherwise, return the response as normal
        return response
