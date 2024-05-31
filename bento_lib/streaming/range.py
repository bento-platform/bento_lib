import re

from .exceptions import StreamingRangeNotSatisfiable, StreamingBadRange

__all__ = ["parse_range_header"]


BYTE_RANGE_INTERVAL_SPLIT = re.compile(r",\s*")
BYTE_RANGE_START_ONLY = re.compile(r"^(\d+)-$")
BYTE_RANGE_START_END = re.compile(r"^(\d+)-(\d+)$")
BYTE_RANGE_SUFFIX = re.compile(r"^-(\d+)$")


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
        int1_start, int1_end = int1

        # Order of these checks is important - we want to give a 416 if start/end is beyond content length (which also
        # results in an inverted interval)

        if int1_start >= content_length:
            # both ends of the range are 0-indexed, inclusive - so it starts at 0 and ends at content_length - 1
            if refget_mode:  # sigh... GA4GH moment
                raise StreamingBadRange(f"start is beyond content length: {int1_start} >= {content_length}")
            raise StreamingRangeNotSatisfiable(f"not satisfiable: {int1_start} >= {content_length}", content_length)

        if int1_end >= content_length:
            # both ends of the range are 0-indexed, inclusive - so it starts at 0 and ends at content_length - 1
            if refget_mode:  # sigh... GA4GH moment
                raise StreamingBadRange(f"end is beyond content length: {int1_end} >= {content_length}")
            raise StreamingRangeNotSatisfiable(f"not satisfiable: {int1_end} >= {content_length}", content_length)

        if not refget_mode and int1_start > int1_end:
            raise StreamingRangeNotSatisfiable(f"inverted interval: {int1}", content_length)

        if i < n_intervals - 1:
            int2 = intervals[i + 1]
            int2_start, int2_end = int2

            if int1_end >= int2_start:
                raise StreamingRangeNotSatisfiable(f"intervals overlap: {int1}, {int2}", content_length)

    return tuple(intervals)
