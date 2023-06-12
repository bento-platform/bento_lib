from django.http import JsonResponse, HttpRequest, HttpResponse
from django.utils.decorators import async_only_middleware
from typing import Awaitable, Callable

from bento_lib.responses.errors import http_error
from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.base import BaseAuthMiddleware

__all__ = [
    "DjangoAuthMiddleware",
]


class DjangoAuthMiddleware(BaseAuthMiddleware):
    def get_authz_header_value(self, request: HttpRequest) -> str | None:
        return request.headers.get("Authorization")

    @staticmethod
    def mark_authz_done(request: HttpRequest):
        request.bento_determined_authz = True

    def make_django_middleware(self):
        @async_only_middleware
        def inner_middleware(get_response: Callable[[HttpRequest], Awaitable[HttpResponse]]):
            async def handle_request(request: HttpRequest) -> HttpResponse:
                return await self.call(get_response, request)
            return handle_request

    def _make_auth_error(self, e: BentoAuthException) -> JsonResponse:
        return JsonResponse(
            http_error(e.status_code, e.message, drs_compat=self._drs_compat, sr_compat=self._sr_compat),
            status_code=e.status_code)

    async def call(
        self,
        get_response: Callable[[HttpRequest], Awaitable[HttpResponse]],
        request: HttpRequest,
    ) -> HttpResponse:
        if not self.enabled:
            return await get_response(request)

        request.bento_determined_authz = False

        try:
            response = await get_response(request)  # We've just crammed a new property in there... no state object
            if not request.bento_determined_authz:
                # Next in response chain didn't properly think about auth; return 403
                return self._make_auth_error(BentoAuthException("Forbidden", status_code=403))

        except BentoAuthException as e:
            self.mark_authz_done(request)
            return self._make_auth_error(e)

        # Otherwise, return the response as normal
        return response
