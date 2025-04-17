import logging
from structlog.stdlib import BoundLogger, get_logger

__all__ = ["internal_logger"]

logging.basicConfig(level=logging.NOTSET)

internal_logger: BoundLogger = get_logger("bento_lib")
