import logging

__all__ = [
    "log_level_from_str",
]


log_level_str_to_log_level = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def log_level_from_str(level: str, default: int = logging.INFO) -> int:
    return log_level_str_to_log_level.get(level.lower(), default)
