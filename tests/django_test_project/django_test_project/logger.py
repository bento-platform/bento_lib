import structlog.stdlib
from bento_lib.logging.structured.django import BentoDjangoAccessLoggerMiddleware

__all__ = ["logger", "access_middleware"]

logger = structlog.stdlib.get_logger("test.logger")

access = BentoDjangoAccessLoggerMiddleware(
    access_logger=structlog.stdlib.get_logger("test.access"),
    service_logger=logger,
)
access_middleware = access.make_django_middleware()
