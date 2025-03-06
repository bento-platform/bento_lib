import structlog
import time
from fastapi import Request, Response
from uvicorn.protocols.utils import get_path_with_query_string

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
        response: Response = Response(status_code=500)

        try:
            response = await call_next(request)
        except Exception as e:  # pragma: no cover
            await service_logger.aexception("uncaught exception", exc_info=e)
        finally:
            # When the response has finished or errored out, write the access log message:

            duration = time.perf_counter_ns() - start_time

            status_code = response.status_code
            # noinspection PyTypeChecker
            url = get_path_with_query_string(request.scope)
            client_host = request.client.host
            client_port = request.client.port
            http_method = request.method
            http_version = request.scope["http_version"]

            await access_logger.ainfo(
                # The message format mirrors the original uvicorn access message, which we aim to replace here with
                # something more structured.
                f"{client_host}:{client_port} - \"{http_method} {url} HTTP/{http_version}\" {status_code}",
                # HTTP information, extracted from the request and response objects:
                http={
                    "url": url,
                    "status_code": status_code,
                    "method": http_method,
                    "version": http_version,
                },
                # Network information, extracted from the request object:
                network={"client": {"host": client_host, "port": client_port}},
                # Duration in nanoseconds, computed in-middleware:
                duration=duration,
            )

            return response

    return access_log_middleware
