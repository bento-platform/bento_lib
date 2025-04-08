import structlog
import time
from fastapi import Request, Response, status
from uvicorn.protocols.utils import get_path_with_query_string

from .common import LogHTTPInfo, LogNetworkInfo, LogNetworkClientInfo, log_access

__all__ = [
    "build_structlog_fastapi_middleware",
]

# For use in FastAPI, also see /docs/logging/fastapi_structlog.md


def build_structlog_fastapi_middleware(service_kind: str):
    """
    Helper to build an access-logging middleware for a FastAPI service, formatting access log messages using structlog.
    :param service_kind: Bento Service Kind (e.g., "reference") for the service installing this middleware.
    :return: Access log middleware function for use in a FastAPI instance.
    """

    access_logger = structlog.stdlib.get_logger(f"{service_kind}.access")
    service_logger = structlog.stdlib.get_logger(f"{service_kind}.logger")

    async def access_log_middleware(request: Request, call_next) -> Response:
        start_time = time.perf_counter_ns()

        # To return if an exception occurs while calling the next in the middleware chain
        response: Response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            response = await call_next(request)
        except Exception as e:  # pragma: no cover
            await service_logger.aexception("uncaught exception", exc_info=e)
        finally:
            # When the response has finished or errored out, write the access log message:
            # noinspection PyTypeChecker
            await log_access(
                access_logger,
                start_time,
                http_info=LogHTTPInfo(
                    url=get_path_with_query_string(request.scope),
                    status_code=response.status_code,
                    method=request.method,
                    version=request.scope["http_version"],
                ),
                network_info=LogNetworkInfo(
                    client=LogNetworkClientInfo(host=request.client.host, port=request.client.port)
                ),
            )

            return response

    return access_log_middleware
