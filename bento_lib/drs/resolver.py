from datetime import datetime

from .utils import decode_drs_uri, fetch_drs_record_by_uri, fetch_drs_record_by_uri_async

__all__ = [
    "DrsResolver",
]


class DrsResolver:
    def __init__(self, cache_ttl: float = 900.0):
        """
        Constructor for a DrsResolver object, which is used to fetch and cache DRS records by their drs://-schemed URI.
        :param cache_ttl: How long (in seconds) a cache entry is valid for.
        """
        self._cache_ttl: float = cache_ttl
        self._drs_record_cache: dict[str, tuple[float, dict]] = {}

    @staticmethod
    def decode_drs_uri(drs_uri: str) -> str:
        """
        This is just a wrapper for bento_lib.drs.utils.decode_drs_uri.
        :param drs_uri: The drs://-schemed URI for the DRS object.
        :return: The HTTP URI for the DRS object specified.
        """
        return decode_drs_uri(drs_uri)

    def fetch_drs_record_by_uri(self, drs_uri: str) -> dict:
        """
        Fetches and, for a time, caches a DRS record using its drs://-schemed URI.
        Cache is shared between this function and its asynchronous version.
        :param drs_uri: A resolvable drs://-schemed URI for a DRS object record.
        :return: The fetched record dictionary.
        """

        now = datetime.now().timestamp()

        cache_record = self._drs_record_cache.get(drs_uri)
        if cache_record is not None and now - cache_record[0] <= self._cache_ttl:
            return cache_record[1]

        res = fetch_drs_record_by_uri(drs_uri)
        self._drs_record_cache[drs_uri] = (now, res)
        return res

    async def fetch_drs_record_by_uri_async(self, drs_uri: str, session_kwargs: dict | None = None) -> dict:
        """
        Asynchronously fetches and, for a time, caches a DRS record using its drs://-schemed URI.
        Cache is shared between this function and its synchronous version.
        :param drs_uri: A resolvable drs://-schemed URI for a DRS object record.
        :param session_kwargs: Optional dictionary of parameters to pass to the aiohttp.ClientSession constructor.
        :return: The fetched record dictionary.
        """

        now = datetime.now().timestamp()

        cache_record = self._drs_record_cache.get(drs_uri)
        if cache_record is not None and now - cache_record[0] <= self._cache_ttl:
            return cache_record[1]

        res = await fetch_drs_record_by_uri_async(drs_uri, session_kwargs)
        self._drs_record_cache[drs_uri] = (now, res)
        return res
