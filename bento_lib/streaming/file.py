import aiofiles
import aiofiles.os
import pathlib

from .range import validate_interval

__all__ = ["stream_file"]


# TODO: support multipart/byterange responses somehow (generator of generators?)


async def stream_file(
    path: pathlib.Path,
    interval: tuple[int, int] | None,
    chunk_size: int,
    yield_content_length_as_first_8: bool = False,
    file_size: int | None = None,
    refget_mode: bool = False,
):
    """
    Stream the contents of a file, optionally yielding the content length as the first 8 bytes of the stream.
    Coordinate parameters are 0-based and inclusive, e.g., 0-10 yields the first 11 bytes. This matches the format of
    HTTP range headers.
    :param path: The path to the file to stream from.
    :param interval: Inclusive, 0-based byte interval to stream. If None, the whole file is streamed instead.
    :param chunk_size: The maximum number of bytes to read/yield at a time while streaming the file.
    :param yield_content_length_as_first_8: Whether to yield the response size as the first byte chunk (8 bytes,
           big-endian encoded) of the stream.
    :param file_size: The whole file's size, if already known. If this has already been calculated/stored, this saves a
           stat() call.
    :param refget_mode: Whether to raise Refget-compliant errors, rather than correct errors (GA4GH...), i.e.,
           400 instead of 416 for past-EOF errors.
    """

    final_file_size: int = file_size or (await aiofiles.os.stat(path)).st_size
    final_interval = interval if interval else (0, final_file_size - 1)

    # Strictly enforce interval order, since we currently can't handle inverted intervals.
    validate_interval(final_interval, final_file_size, refget_mode=refget_mode, enforce_not_inverted=True)

    start, end = final_interval
    response_size: int = end - start + 1  # Inclusive interval - need to add 1

    if yield_content_length_as_first_8:
        yield response_size.to_bytes(8, "big")

    async with aiofiles.open(path, "rb") as ff:
        # First, skip over <start> bytes to get to the beginning of the range
        await ff.seek(start)

        byte_offset: int = start
        while True:
            # Add a 1 to the amount to read if it's below chunk size, because the last coordinate is inclusive.
            data = await ff.read(min(chunk_size, end + 1 - byte_offset))
            byte_offset += len(data)
            yield data

            # If we've hit the end of the file and are reading empty byte strings, or we've reached the
            # end of our range (inclusive), then escape the loop.
            # This is guaranteed to terminate with a finite-sized file.
            if not data or byte_offset > end:
                break
