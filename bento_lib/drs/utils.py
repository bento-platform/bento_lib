import requests
import sys

from urllib.parse import urlparse

from typing import Optional

__all__ = [
    "DrsInvalidScheme",
    "DrsRequestError",
    "get_file_access_method_if_any",
    "drs_uri_to_record"
]


class DrsInvalidScheme(Exception):
    pass


class DrsRequestError(Exception):
    pass


def get_file_access_method_if_any(drs_object_record: dict) -> Optional[dict]:
    """
    Gets a file path access method from a DRS object, if one exists.
    :param drs_object_record: The record for the DRS object, fetched from the instance.
    :return: The file path to the object's bytes, if one exists.
    """
    return next((a for a in drs_object_record.get("access_methods", []) if a.get("type", None) == "file"), None)


def _decode_drs_uri(drs_uri: str, internal_drs_base_url: Optional[str] = None) -> str:
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


def drs_uri_to_record(drs_uri: str, internal_drs_base_url: Optional[str] = None) -> Optional[dict]:
    """
    Given a URI in the format drs://<hostname>/<object-id>, decodes it into an
    HTTP URL and fetches the object metadata.
    :param drs_uri: The URI of the object to fetch.
    :param internal_drs_base_url: An optional override hard-coded DRS base URL to use, for container networking etc.
    :return: The fetched DRS object metadata.
    """

    # TODO: Translation dictionary for internal DRS hostnames, to avoid overriding EVERY DRS host.

    decoded_object_uri = _decode_drs_uri(drs_uri, internal_drs_base_url)
    print(f"[Bento Lib] Attempting to fetch {decoded_object_uri}", flush=True)
    drs_res = requests.get(decoded_object_uri)

    if drs_res.status_code != 200:
        print(f"[Bento Lib] Could not fetch: '{decoded_object_uri}'", file=sys.stderr, flush=True)
        print(f"\tAttempted URL: {decoded_object_uri} (status: {drs_res.status_code})", file=sys.stderr, flush=True)
        raise DrsRequestError(f"Could not fetch '{decoded_object_uri}' (status: {drs_res.status_code})")

    # TODO: Handle JSON parse errors
    # TODO: Schema for DRS response

    return drs_res.json()
