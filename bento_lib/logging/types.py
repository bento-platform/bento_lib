from logging import Logger
from structlog.stdlib import BoundLogger
from typing import Literal

__all__ = [
    "LogLevelLiteral",
    "StdOrBoundLogger",
]


type LogLevelLiteral = Literal["debug", "info", "warning", "error"]
type StdOrBoundLogger = Logger | BoundLogger
