import re

from .exceptions import StreamingRangeNotSatisfiable, StreamingBadRange

__all__ = ["validate_interval", "parse_range_header"]


BYTE_RANGE_INTERVAL_SPLIT = re.compile(r",\s*")
BYTE_RANGE_START_ONLY = re.compile(r"^(\d+)-$")
BYTE_RANGE_START_END = re.compile(r"^(\d+)-(\d+)$")
BYTE_RANGE_SUFFIX = re.compile(r"^-(\d+)$")


def validate_interval(
    interval: tuple[int, int],
    content_length: int,
    refget_mode: bool = False,
    enforce_not_inverted: bool | None = None,
) -> None:
    """
    Validates a byte interval on a particular content length. Raises an exception (a subclass of
    bento_lib.streaming.exceptions.StreamingException) if the interval is invalid. Raising for inverted intervals is
    optional but on by default unless Refget mode is turned on, in which case it is off unless otherwise set.
    :param interval: A 0-based, inclusive byte interval to validate: a tuple of start byte index, end byte index.
    :param content_length: The total content length of the bytes the interval is for.
    :param refget_mode: Whether to generate Refget-compatible errors rather than standard errors for ranges which go
           past the end of the content bytes.
    :param enforce_not_inverted: Whether to enforce interval order (i.e., start <= end). If None, falls back to
           enforcing only when not in Refget mode.
    :return: None. An exception is raised if the interval is invalid (see bento_lib.streaming.exceptions).
    """

    int_start, int_end = interval

    # Order of these checks is important - we want to give a 416 if start/end is beyond content length (which also
    # results in an inverted interval)

    if int_start >= content_length:
        # both ends of the range are 0-indexed, inclusive - so it starts at 0 and ends at content_length - 1
        if refget_mode:  # sigh... GA4GH moment
            raise StreamingBadRange(f"start is beyond content length: {int_start} >= {content_length}")
        raise StreamingRangeNotSatisfiable(
            f"not satisfiable: {int_start} >= {content_length}", "start>=length", content_length
        )

    if int_end >= content_length:
        # both ends of the range are 0-indexed, inclusive - so it starts at 0 and ends at content_length - 1
        if refget_mode:  # sigh... GA4GH moment
            raise StreamingBadRange(f"end is beyond content length: {int_end} >= {content_length}")
        raise StreamingRangeNotSatisfiable(
            f"not satisfiable: {int_end} >= {content_length}", "end>=length", content_length
        )

    should_check_inverted = (not refget_mode) if enforce_not_inverted is None else enforce_not_inverted
    if should_check_inverted and int_start > int_end:
        raise StreamingRangeNotSatisfiable(f"inverted interval: {interval}", "inverted", content_length)


def parse_range_header(
    range_header: str | None, content_length: int, refget_mode: bool = False
) -> tuple[tuple[int, int], ...]:
    """
    Parse a range header (given a particular content length) into a validated series of sorted, non-overlapping
    start/end-inclusive intervals.
    """

    if range_header is None:
        return ((0, content_length - 1),)

    intervals: list[tuple[int, int]] = []

    if not range_header.startswith("bytes="):
        raise StreamingBadRange("only bytes range headers are supported")

    intervals_str = range_header.removeprefix("bytes=")

    # Cases: start- | start-end | -suffix, [start- | start-end | -suffix], ...

    intervals_str_split = BYTE_RANGE_INTERVAL_SPLIT.split(intervals_str)

    for iv in intervals_str_split:
        if m := BYTE_RANGE_START_ONLY.match(iv):
            intervals.append((int(m.group(1)), content_length - 1))
        elif m := BYTE_RANGE_START_END.match(iv):
            intervals.append((int(m.group(1)), int(m.group(2))))
        elif m := BYTE_RANGE_SUFFIX.match(iv):
            inclusive_content_length = content_length - 1
            suffix_length = int(m.group(1))  # suffix: -500 === last 500:
            intervals.append((max(inclusive_content_length - suffix_length + 1, 0), inclusive_content_length))
        else:
            raise StreamingBadRange("byte range did not match any pattern")

    intervals.sort()
    n_intervals: int = len(intervals)

    # validate intervals are not inverted and do not overlap each other:
    for i, int1 in enumerate(intervals):
        validate_interval(int1, content_length, refget_mode=refget_mode)

        _, int1_end = int1
        if i < n_intervals - 1:
            int2 = intervals[i + 1]
            int2_start, int2_end = int2

            if int1_end >= int2_start:
                raise StreamingRangeNotSatisfiable(f"intervals overlap: {int1}, {int2}", "overlap", content_length)

    return tuple(intervals)
