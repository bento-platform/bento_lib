import logging
from typing import Literal

__all__ = [
    "LogLevelLiteral",
    "log_level_from_str",
]


LogLevelLiteral = Literal["debug", "info", "warning", "error"]


log_level_str_to_log_level: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def log_level_from_str(level: str, default: int = logging.INFO) -> int:
    return log_level_str_to_log_level.get(level.lower(), default)
