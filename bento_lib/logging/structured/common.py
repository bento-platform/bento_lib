import time
from pydantic import BaseModel
from structlog.stdlib import BoundLogger

__all__ = [
    "LogHTTPInfo",
    "LogNetworkInfo",
    "LogNetworkClientInfo",
    "log_access",
]


class LogHTTPInfo(BaseModel):
    url: str
    status_code: int
    method: str
    version: str | None  # If None, not known (in the case of the Django development server)


class LogNetworkClientInfo(BaseModel):
    host: str | None
    port: int | None


class LogNetworkInfo(BaseModel):
    client: LogNetworkClientInfo


def _client_str(client: LogNetworkClientInfo) -> str:
    return f"{client.host or ''}{':' + str(client.port) if client.port else ''}"


def _http_str(http: LogHTTPInfo) -> str:
    http_str = f"HTTP/{http.version}" if http.version else "HTTP"
    return f'"{http.method} {http.url} {http_str}" {http.status_code}'


async def log_access(logger: BoundLogger, start_time_ns: int, http_info: LogHTTPInfo, network_info: LogNetworkInfo):
    # When the response has finished or errored out, write the access log message:

    duration = time.perf_counter_ns() - start_time_ns

    await logger.ainfo(
        # The message format mirrors the original uvicorn access message, which we aim to replace here with
        # something more structured.
        f"{_client_str(network_info.client) or '<unknown>'} - {_http_str(http_info)}",
        # HTTP information, extracted from the request and response objects:
        http=http_info.model_dump(mode="json", exclude_none=True),
        # Network information, extracted from the request object:
        network=network_info.model_dump(mode="json"),
        # Duration in nanoseconds, computed in-middleware:
        duration=duration,
    )
