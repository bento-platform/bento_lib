__all__ = [
    "StreamingRangeNotSatisfiable",
    "StreamingBadRange",
    "StreamingProxyingError",
    "StreamingResponseExceededLimit",
    "StreamingBadURI",
    "StreamingUnsupportedURIScheme",
]


class StreamingRangeNotSatisfiable(Exception):
    def __init__(self, message: str, n_bytes: int | None):
        self._n_bytes: int | None = n_bytes
        super().__init__(message)

    @property
    def n_bytes(self) -> int:
        return self._n_bytes


class StreamingBadRange(Exception):
    pass


class StreamingProxyingError(Exception):
    pass


class StreamingResponseExceededLimit(Exception):
    pass


class StreamingBadURI(Exception):
    pass


class StreamingUnsupportedURIScheme(Exception):
    pass
