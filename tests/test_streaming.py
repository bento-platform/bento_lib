import pytest
from typing import Type

from bento_lib.streaming import exceptions as s, range as r

CONTENT_LENGTH = 10000


def test_streaming_exceptions():
    e = s.StreamingRangeNotSatisfiable("Not satisfiable", 100)
    assert e.n_bytes == 100
    assert str(e) == "Not satisfiable"


@pytest.mark.parametrize(
    "range_header,refget_mode,exc",
    [
        ("bites=0-100", False, s.StreamingBadRange),
        ("bytes=500", False, s.StreamingBadRange),
        ("bytes=100-0", False, s.StreamingRangeNotSatisfiable),
        ("bytes=abc-", False, s.StreamingBadRange),
        ("bytes=-10-20", False, s.StreamingBadRange),
        ("bytes=5bc-600", False, s.StreamingBadRange),
        ("bytes=0-50,100-0", False, s.StreamingRangeNotSatisfiable),  # terminal inverted range
        ("bytes=0-50,30-100", False, s.StreamingRangeNotSatisfiable),  # don't support overlapping ranges
        ("bytes=0-30,30-100", False, s.StreamingRangeNotSatisfiable),  # don't support overlapping ranges (inclusive)
        ("bytes=0-30,35-33,40-100", False, s.StreamingRangeNotSatisfiable),  # non-terminal inverted range
        ("bytes=100000-", False, s.StreamingRangeNotSatisfiable),  # past end of file
        ("bytes=0-100000", False, s.StreamingRangeNotSatisfiable),  # past end of file
        # Refget mode: 400 instead of 416 for past-EOF errors
        ("bytes=100000-", True, s.StreamingBadRange),  # past end of file
        ("bytes=0-100000", True, s.StreamingBadRange),  # past end of file
    ],
)
def test_parse_range_header_errors(range_header: str, refget_mode: bool, exc: Type[Exception]):
    with pytest.raises(exc):
        r.parse_range_header(range_header, CONTENT_LENGTH, refget_mode=refget_mode)


@pytest.mark.parametrize(
    "range_header,intervals",
    [
        (None, ((0, CONTENT_LENGTH - 1),)),
        ("bytes=0-100", ((0, 100),)),
        ("bytes=0-", ((0, CONTENT_LENGTH - 1),)),
        ("bytes=5-10", ((5, 10),)),
        ("bytes=5-10, 15-20", ((5, 10), (15, 20))),
        ("bytes=5-10, 15-", ((5, 10), (15, CONTENT_LENGTH - 1))),
        ("bytes=-500", ((CONTENT_LENGTH - 500, CONTENT_LENGTH - 1),)),
        ("bytes=0-100, -500", ((0, 100), (CONTENT_LENGTH - 500, CONTENT_LENGTH - 1),)),
    ],
)
def test_parse_range_header_valid(range_header: str | None, intervals: tuple[tuple[int, int], ...]):
    assert r.parse_range_header(range_header, CONTENT_LENGTH) == intervals
