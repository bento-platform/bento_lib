import time

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from structlog.stdlib import BoundLogger
from typing import Awaitable, Callable

from .common import LogHTTPInfo, LogNetworkInfo, LogNetworkClientInfo, log_access

__all__ = [
    "BentoDjangoAccessLoggerMiddleware",
]


class BentoDjangoAccessLoggerMiddleware:
    """
    Quasi-factory class to build an access-logging Django middleware class via the make_django_middleware() method.
    Similar to the authorization middleware for Django/FastAPI, we set this up as a "middleware factory" so that we can
    inject logger instances.
    """

    def __init__(self, access_logger: BoundLogger, service_logger: BoundLogger):
        self._access_logger = access_logger
        self._service_logger = service_logger

    def make_django_middleware(self):
        class InnerMiddleware:
            async_capable = True
            sync_capable = False

            # noinspection PyMethodParameters
            def __init__(inner_self, get_response: Callable[[HttpRequest], Awaitable[HttpResponse]]):
                inner_self.get_response = get_response
                if iscoroutinefunction(inner_self.get_response):  # pragma: no cover
                    markcoroutinefunction(inner_self)

            # noinspection PyMethodParameters
            async def __call__(inner_self, request: HttpRequest):
                start_time = time.perf_counter_ns()

                response: HttpResponse = HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                try:
                    response = await inner_self.get_response(request)
                except Exception as e:  # pragma: no cover
                    await self._service_logger.aexception("uncaught exception", exc_info=e)
                finally:
                    # When the response has finished or errored out, write the access log message:
                    # noinspection PyTypeChecker
                    await log_access(
                        self._access_logger,
                        start_time,
                        http_info=LogHTTPInfo(
                            url=request.get_full_path(),
                            status_code=response.status_code,
                            method=request.method,
                            version=None,
                        ),
                        network_info=LogNetworkInfo(
                            client=LogNetworkClientInfo(
                                # Match what uvicorn shows:
                                host=request.META.get("REMOTE_HOST"),
                                port=request.META.get("REMOTE_PORT"),
                            )
                        ),
                    )

                    return response

        return InnerMiddleware
