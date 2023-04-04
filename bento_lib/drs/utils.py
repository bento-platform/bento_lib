import aiohttp
import requests
import sys

from urllib.parse import urlparse

from typing import Optional

__all__ = [
    "DrsInvalidScheme",
    "DrsRequestError",

    "get_access_method_of_type",
    "decode_drs_uri",
    "fetch_drs_record_by_uri"
]


class DrsInvalidScheme(Exception):
    pass


class DrsRequestError(Exception):
    pass


def get_access_method_of_type(drs_object_record: dict, access_type: str, default=None):
    """
    Gets an access method of specified type from a DRS object, if one with the type exists.
    :param drs_object_record: The record for the DRS object, fetched from the instance.
    :param access_type: The access type to try and find in the object record.
    :param default: The value to return if the access method is not found.
    :return: The access method of the specified type for the object's bytes, if one exists.
    """
    return next((a for a in drs_object_record.get("access_methods", []) if a.get("type", None) == access_type), default)


def decode_drs_uri(drs_uri: str, internal_drs_base_url: Optional[str] = None) -> str:
    """
    Given a DRS URI and possibly an override for the DRS service URL, returns
    the decoded HTTP URL for the DRS object.
    :param drs_uri: The drs://-schemed URI for the DRS object.
    :param internal_drs_base_url: An optional override hard-coded DRS base URL to use, for container networking etc.
    :return: The HTTP URI for the DRS object specified.
    """

    parsed_drs_uri = urlparse(drs_uri)

    if parsed_drs_uri.scheme != "drs":
        print(f"[Bento Lib] Invalid scheme: '{parsed_drs_uri.scheme}'",
              file=sys.stderr, flush=True)
        raise DrsInvalidScheme(f"Encountered invalid DRS scheme: {parsed_drs_uri.scheme}")

    drs_base_path = internal_drs_base_url.rstrip("/") if internal_drs_base_url else f"https://{parsed_drs_uri.netloc}"
    return f"{drs_base_path}/ga4gh/drs/v1/objects/{parsed_drs_uri.path.split('/')[-1]}"


def fetch_drs_record_by_uri(drs_uri: str, internal_drs_base_url: Optional[str] = None) -> Optional[dict]:
    """
    Given a URI in the format drs://<hostname>/<object-id>, decodes it into an
    HTTP URL and fetches the object metadata.
    :param drs_uri: The URI of the object to fetch.
    :param internal_drs_base_url: An optional override hard-coded DRS base URL to use, for container networking etc.
    :return: The fetched DRS object metadata.
    """

    # TODO: Translation dictionary for internal DRS hostnames, to avoid overriding EVERY DRS host.

    decoded_object_uri = decode_drs_uri(drs_uri, internal_drs_base_url)
    print(f"[Bento Lib] Attempting to fetch {decoded_object_uri}", flush=True)
    params = {"internal_path": "true"} if internal_drs_base_url else {}
    drs_res = requests.get(decoded_object_uri, params=params)

    if drs_res.status_code != 200:
        print(f"[Bento Lib] Could not fetch: '{decoded_object_uri}'", file=sys.stderr, flush=True)
        print(f"\tAttempted URL: {decoded_object_uri} (status: {drs_res.status_code})", file=sys.stderr, flush=True)
        raise DrsRequestError(f"Could not fetch '{decoded_object_uri}' (status: {drs_res.status_code})")

    # TODO: Handle JSON parse errors
    # TODO: Schema for DRS response

    return drs_res.json()


async def fetch_drs_record_by_uri_async(drs_uri: str, internal_drs_base_url: Optional[str] = None) -> Optional[dict]:
    """
    Given a URI in the format drs://<hostname>/<object-id>, decodes it into an
    HTTP URL and asynchronously fetches the object metadata.
    :param drs_uri: The URI of the object to fetch.
    :param internal_drs_base_url: An optional override hard-coded DRS base URL to use, for container networking etc.
    :return: The fetched DRS object metadata.
    """

    # TODO: Translation dictionary for internal DRS hostnames, to avoid overriding EVERY DRS host.

    decoded_object_uri = decode_drs_uri(drs_uri, internal_drs_base_url)
    print(f"[Bento Lib] Attempting to fetch {decoded_object_uri}", flush=True)

    params = {"internal_path": "true"} if internal_drs_base_url else {}
    async with aiohttp.ClientSession() as session:
        async with session.get(decoded_object_uri, params=params) as drs_res:
            if drs_res.status != 200:
                print(f"[Bento Lib] Could not fetch: '{decoded_object_uri}'", file=sys.stderr, flush=True)
                print(f"\tAttempted URL: {decoded_object_uri} (status: {drs_res.status})", file=sys.stderr, flush=True)
                raise DrsRequestError(f"Could not fetch '{decoded_object_uri}' (status: {drs_res.status})")

            # TODO: Handle JSON parse errors
            # TODO: Schema for DRS response

            return await drs_res.json()
