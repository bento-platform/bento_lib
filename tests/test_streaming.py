import pytest
from typing import Type

from bento_lib.streaming import exceptions as s, file as f, range as r
from .common import SARS_COV_2_FASTA_PATH

DUMMY_CONTENT_LENGTH = 10000


def test_streaming_exceptions():
    e = s.StreamingRangeNotSatisfiable("Not satisfiable", "start>=length", 100)
    assert e.n_bytes == 100
    assert str(e) == "Not satisfiable"
    assert e.reason == "start>=length"


validate_interval_params: list[
    tuple[tuple[int, int], bool, bool | None, Type[Exception], s.RangeNotSatisfiableReason | None]
] = [
    ((100, 0), False, None, s.StreamingRangeNotSatisfiable, "inverted"),  # inverted range
    ((100, 0), False, True, s.StreamingRangeNotSatisfiable, "inverted"),  # inverted range
    ((0, 100000), False, None, s.StreamingRangeNotSatisfiable, "end>=length"),  # past end of file
    ((100000, 200000), False, None, s.StreamingRangeNotSatisfiable, "start>=length"),  # past end of file
    # Refget mode: 400 instead of 416 for past-EOF errors
    ((0, 100000), True, None, s.StreamingBadRange, None),  # past end of file
    ((100000, 200000), True, None, s.StreamingBadRange, None),  # past end of file
    ((100, 0), True, True, s.StreamingRangeNotSatisfiable, "inverted"),  # inverted range
]


@pytest.mark.parametrize("interval,refget_mode,enforce_interval_order,exc,reason", validate_interval_params)
def test_validate_interval_errors(
    interval: tuple[int, int],
    refget_mode: bool,
    enforce_interval_order: bool | None,
    exc: Type[Exception],
    reason: s.RangeNotSatisfiableReason | None,
):
    with pytest.raises(exc) as e:
        r.validate_interval(
            interval, DUMMY_CONTENT_LENGTH, refget_mode=refget_mode, enforce_not_inverted=enforce_interval_order
        )

    if reason is not None:
        assert e.value.reason == reason


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
        r.parse_range_header(range_header, DUMMY_CONTENT_LENGTH, refget_mode=refget_mode)


@pytest.mark.parametrize(
    "range_header,intervals",
    [
        (None, ((0, DUMMY_CONTENT_LENGTH - 1),)),
        ("bytes=0-100", ((0, 100),)),
        ("bytes=0-", ((0, DUMMY_CONTENT_LENGTH - 1),)),
        ("bytes=5-10", ((5, 10),)),
        ("bytes=5-10, 15-20", ((5, 10), (15, 20))),
        ("bytes=5-10, 15-", ((5, 10), (15, DUMMY_CONTENT_LENGTH - 1))),
        ("bytes=-500", ((DUMMY_CONTENT_LENGTH - 500, DUMMY_CONTENT_LENGTH - 1),)),
        ("bytes=0-100, -500", ((0, 100), (DUMMY_CONTENT_LENGTH - 500, DUMMY_CONTENT_LENGTH - 1),)),
    ],
)
def test_parse_range_header_valid(range_header: str | None, intervals: tuple[tuple[int, int], ...]):
    assert r.parse_range_header(range_header, DUMMY_CONTENT_LENGTH) == intervals


TEST_CHUNK_SIZE = 128


@pytest.mark.asyncio()
async def test_file_streaming():
    stream = f.stream_file(SARS_COV_2_FASTA_PATH, None, TEST_CHUNK_SIZE)

    stream_contents = b""
    async for chunk in stream:
        stream_contents += chunk

    with open(SARS_COV_2_FASTA_PATH, "rb") as fh:
        fc = fh.read()

    assert fc == stream_contents
    file_length = len(fc)

    # ---

    stream = f.stream_file(SARS_COV_2_FASTA_PATH, None, TEST_CHUNK_SIZE, yield_content_length_as_first_8=True)
    content_length = int.from_bytes(await anext(stream), byteorder="big")
    assert content_length == file_length
    async for chunk in stream:
        assert isinstance(chunk, bytes)


with open(SARS_COV_2_FASTA_PATH, "rb") as cfh:
    COVID_FASTA_BYTES = cfh.read()


@pytest.mark.parametrize(
    "interval,expected,size",
    [
        ((0, 10), b">MN908947.3", 11),
        ((5, 10), b"8947.3", None),
        ((10, len(COVID_FASTA_BYTES) - 1), COVID_FASTA_BYTES[10:], None),
        ((0, 2), b">MN", 3),  # TODO: ignores everything except first range
        ((256, 512), COVID_FASTA_BYTES[256:513], 257),
        ((0, len(COVID_FASTA_BYTES) - 1), COVID_FASTA_BYTES, None),
    ],
)
@pytest.mark.asyncio()
async def test_file_streaming_ranges(interval: tuple[int, int], expected: bytes, size: int | None):
    stream = f.stream_file(
        SARS_COV_2_FASTA_PATH, interval, TEST_CHUNK_SIZE, yield_content_length_as_first_8=size is not None
    )

    if size is not None:
        cl = int.from_bytes(await anext(stream), byteorder="big")
        assert cl == size

    stream_contents = b""
    async for chunk in stream:
        stream_contents += chunk

    assert stream_contents == expected


@pytest.mark.asyncio()
async def test_file_streaming_range_errors():
    with pytest.raises(s.StreamingRangeNotSatisfiable) as e:
        stream = f.stream_file(SARS_COV_2_FASTA_PATH, (1000000000, 1000000010), TEST_CHUNK_SIZE)  # past EOF
        await anext(stream)
        assert getattr(e, "reason") == "start>=length"

    with pytest.raises(s.StreamingRangeNotSatisfiable):
        stream = f.stream_file(SARS_COV_2_FASTA_PATH, (0, 10000000000), TEST_CHUNK_SIZE)  # past EOF
        await anext(stream)
        assert getattr(e, "reason") == "end>=length"

    with pytest.raises(s.StreamingRangeNotSatisfiable):
        stream = f.stream_file(SARS_COV_2_FASTA_PATH, (10000, 5000), TEST_CHUNK_SIZE)  # start > end
        await anext(stream)
        assert getattr(e, "reason") == "inverted"

    # Refget mode:

    with pytest.raises(s.StreamingBadRange):
        stream = f.stream_file(SARS_COV_2_FASTA_PATH, (1000000000, 1000000010), TEST_CHUNK_SIZE, refget_mode=True)
        await anext(stream)

    with pytest.raises(s.StreamingBadRange):
        stream = f.stream_file(SARS_COV_2_FASTA_PATH, (0, 10000000000), TEST_CHUNK_SIZE, refget_mode=True)
        await anext(stream)
