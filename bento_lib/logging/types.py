from logging import Logger
from structlog.stdlib import BoundLogger
from typing import Literal

__all__ = [
    "LogLevelLiteral",
    "StdOrBoundLogger",
]


LogLevelLiteral = Literal["debug", "info", "warning", "error"]
StdOrBoundLogger = Logger | BoundLogger
