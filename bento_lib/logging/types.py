from logging import Logger
from typing import Literal

from structlog.stdlib import BoundLogger

__all__ = [
    "LogLevelLiteral",
    "StdOrBoundLogger",
]


type LogLevelLiteral = Literal["debug", "info", "warning", "error"]
type StdOrBoundLogger = Logger | BoundLogger
