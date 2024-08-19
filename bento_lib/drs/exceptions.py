__all__ = [
    "DrsInvalidScheme",
    "DrsRecordNotFound",
    "DrsRequestError",
]


class DrsInvalidScheme(Exception):
    pass


class DrsRecordNotFound(Exception):
    pass


class DrsRequestError(Exception):
    pass
