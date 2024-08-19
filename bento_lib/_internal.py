import logging

__all__ = ["internal_logger"]

logging.basicConfig(level=logging.NOTSET)

internal_logger = logging.getLogger("bento_lib")
