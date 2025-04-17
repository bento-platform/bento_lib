import logging

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import JsonResponse, HttpRequest, HttpResponse
from rest_framework.request import Request as DrfRequest
from typing import Awaitable, Callable

from bento_lib.responses.errors import http_error
from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.base import BaseAuthMiddleware

__all__ = [
    "DjangoAuthMiddleware",
]


class DjangoAuthMiddleware(BaseAuthMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If no logger was passed, create a new logger
        if self._logger is None:
            self._logger = logging.getLogger(__name__)

    def get_authz_header_value(self, request: DrfRequest | HttpRequest) -> str | None:
        return request.headers.get("Authorization")

    @staticmethod
    def mark_authz_done(request: DrfRequest | HttpRequest):
        # noinspection PyProtectedMember
        req = request._request if isinstance(request, DrfRequest) else request
        req.bento_determined_authz = True

    def make_django_middleware(self):
        # noinspection PyMethodParameters
        class InnerMiddleware:
            async_capable = True
            sync_capable = False

            def __init__(inner_self, get_response: Callable[[HttpRequest], Awaitable[HttpResponse]]):
                inner_self.get_response = get_response
                if iscoroutinefunction(inner_self.get_response):  # pragma: no cover
                    markcoroutinefunction(inner_self)

            async def __call__(inner_self, request: HttpRequest) -> HttpResponse:
                return await self.dispatch(inner_self.get_response, request)

            @staticmethod
            def process_exception(request: HttpRequest, exc: Exception):
                if isinstance(exc, BentoAuthException):
                    self.mark_authz_done(request)
                    return self._make_auth_error(exc)
                return None

        return InnerMiddleware

    def _make_auth_error(self, e: BentoAuthException) -> JsonResponse:
        return JsonResponse(
            http_error(
                e.status_code,
                e.message,
                drs_compat=self._drs_compat,
                sr_compat=self._sr_compat,
                beacon_meta_callback=self._beacon_meta_callback,
            ),
            status=e.status_code,
        )

    async def dispatch(
        self,
        get_response: Callable[[HttpRequest], Awaitable[HttpResponse]],
        request: HttpRequest,
    ) -> HttpResponse:
        if not self.enabled:
            return await get_response(request)

        request.bento_determined_authz = False

        # Don't handle BentoAuthException here - middleware handles it elsewhere
        response = await get_response(request)  # We've just crammed a new property in there... no state object

        if not self.enabled or self.request_is_exempt(request.method, request.path):
            # - Skip checks if the authorization middleware is disabled
            # - Allow pre-flight responses through, as well as any configured exempt URLs
            return response

        if not request.bento_determined_authz:
            # Next in response chain didn't properly think about auth; return 403
            return self._make_auth_error(BentoAuthException("Forbidden", status_code=403))

        # Otherwise, return the response as normal
        return response
