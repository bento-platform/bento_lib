from typing import Literal

__all__ = [
    "StreamingException",
    "RangeNotSatisfiableReason",
    "StreamingRangeNotSatisfiable",
    "StreamingBadRange",
    "StreamingProxyingError",
    "StreamingResponseExceededLimit",
    "StreamingBadURI",
    "StreamingUnsupportedURIScheme",
]


class StreamingException(Exception):
    """
    Generic streaming exception / base class for other bento_lib.streaming exceptions.
    """

    pass


RangeNotSatisfiableReason = Literal["start>=length", "end>=length", "inverted", "overlap", "proxied"]


class StreamingRangeNotSatisfiable(StreamingException):
    def __init__(self, message: str, reason: RangeNotSatisfiableReason, n_bytes: int | None):
        self._n_bytes: int | None = n_bytes
        self._reason: RangeNotSatisfiableReason = reason
        super().__init__(message)

    @property
    def reason(self) -> RangeNotSatisfiableReason:
        return self._reason

    @property
    def n_bytes(self) -> int:
        return self._n_bytes


class StreamingBadRange(StreamingException):
    pass


class StreamingProxyingError(StreamingException):
    pass


class StreamingResponseExceededLimit(StreamingException):
    pass


class StreamingBadURI(StreamingException):
    pass


class StreamingUnsupportedURIScheme(StreamingException):
    pass
