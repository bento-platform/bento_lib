import structlog
import time
from fastapi import Request, Response
from uvicorn.protocols.utils import get_path_with_query_string

__all__ = [
    "build_structlog_fastapi_middleware",
]


def build_structlog_fastapi_middleware(service_kind: str):
    access_logger = structlog.stdlib.get_logger(f"{service_kind}.access")
    service_logger = structlog.stdlib.get_logger(f"{service_kind}.logger")

    async def access_log_middleware(request: Request, call_next) -> Response:
        start_time = time.perf_counter_ns()

        try:
            response = await call_next(request)
        except Exception as e:  # pragma: no cover
            await service_logger.aexception("uncaught exception", exc_info=e)
        finally:
            duration = time.perf_counter_ns() - start_time

            status_code = response.status_code
            url = get_path_with_query_string(request.scope)
            client_host = request.client.host
            client_port = request.client.port
            http_method = request.method
            http_version = request.scope["http_version"]

            await access_logger.ainfo(
                # The message format mirrors the original uvicorn access message, which we aim to replace here with
                # something more structured.
                f"{client_host}:{client_port} - \"{http_method} {url} HTTP/{http_version}\" {status_code}",
                http={
                    "url": url,
                    "status_code": status_code,
                    "method": http_method,
                    "version": http_version,
                },
                network={"client": {"host": client_host, "port": client_port}},
                duration=duration,
            )

            return response

    return access_log_middleware
