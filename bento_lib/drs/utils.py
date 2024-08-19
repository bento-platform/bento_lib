import aiohttp
import requests

from urllib.parse import urlparse

from .exceptions import DrsInvalidScheme, DrsRecordNotFound, DrsRequestError

__all__ = [
    "get_access_method_of_type",
    "decode_drs_uri",
    "fetch_drs_record_by_uri",
    "fetch_drs_record_by_uri_async",
]


def get_access_method_of_type(drs_object_record: dict, access_type: str, default=None):
    """
    Gets an access method of specified type from a DRS object, if one with the type exists.
    :param drs_object_record: The record for the DRS object, fetched from the instance.
    :param access_type: The access type to try and find in the object record.
    :param default: The value to return if the access method is not found.
    :return: The access method of the specified type for the object's bytes, if one exists.
    """
    return next((a for a in drs_object_record.get("access_methods", []) if a.get("type", None) == access_type), default)


def decode_drs_uri(drs_uri: str) -> str:
    """
    Given a DRS URI and possibly an override for the DRS service URL, returns
    the decoded HTTP URL for the DRS object.
    :param drs_uri: The drs://-schemed URI for the DRS object.
    :return: The HTTP URI for the DRS object specified.
    """

    parsed_drs_uri = urlparse(drs_uri)

    if parsed_drs_uri.scheme != "drs":
        raise DrsInvalidScheme(f"Encountered invalid DRS scheme: {parsed_drs_uri.scheme}")

    return f"https://{parsed_drs_uri.netloc}/ga4gh/drs/v1/objects/{parsed_drs_uri.path.split('/')[-1]}"


def fetch_drs_record_by_uri(drs_uri: str) -> dict:
    """
    Given a URI in the format drs://<hostname>/<object-id>, decodes it into an
    HTTP URL and fetches the object metadata.
    :param drs_uri: The URI of the object to fetch.
    :return: The fetched DRS object metadata.
    """

    decoded_object_uri = decode_drs_uri(drs_uri)

    drs_res = requests.get(decoded_object_uri)

    if drs_res.status_code == 404:
        raise DrsRecordNotFound(f"Could not find DRS record at '{decoded_object_uri}'")
    elif drs_res.status_code != 200:
        raise DrsRequestError(f"Could not fetch '{decoded_object_uri}' (status: {drs_res.status_code})")

    return drs_res.json()


async def fetch_drs_record_by_uri_async(drs_uri: str, session_kwargs: dict | None = None) -> dict:
    """
    Given a URI in the format drs://<hostname>/<object-id>, decodes it into an
    HTTP URL and asynchronously fetches the object metadata.
    :param drs_uri: The URI of the object to fetch.
    :param session_kwargs: Optional dictionary of parameters to pass to the aiohttp.ClientSession constructor.
    :return: The fetched DRS object metadata.
    """

    decoded_object_uri = decode_drs_uri(drs_uri)

    async with aiohttp.ClientSession(**(session_kwargs or {})) as session:
        async with session.get(decoded_object_uri) as drs_res:
            if drs_res.status == 404:
                raise DrsRecordNotFound(f"Could not find DRS record at '{decoded_object_uri}'")
            elif drs_res.status != 200:
                raise DrsRequestError(f"Could not fetch '{decoded_object_uri}' (status: {drs_res.status})")

            return await drs_res.json()
