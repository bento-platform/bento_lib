import json
import pytest
import responses
import time

from aioresponses import aioresponses
from bento_lib.responses import errors
from bento_lib.drs import exceptions as drs_exceptions, resolver as drs_resolver, utils as drs_utils

TEST_DRS_ID = "dd11912c-3433-4a0a-8a01-3c0699288bef"

TEST_DRS_REPLY_NO_ACCESS = {
    "checksums": [{
        "checksum": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        "type": "sha-256",
    }],
    "created_time": "2021-03-17T21:29:15+00:00",
    "updated_time": "2021-03-17T21:29:15+00:00",
    "id": TEST_DRS_ID,
    "mime_type": "text/plain",
    "self_uri": f"drs://localhost/{TEST_DRS_ID}",
    "size": 4,
}

TEST_DRS_REPLY = {
    **TEST_DRS_REPLY_NO_ACCESS,
    "access_methods": [{
        "type": "file",
        "access_url": "file:///test.txt",
    }],
}


def test_get_access_method():
    assert json.dumps(drs_utils.get_access_method_of_type(TEST_DRS_REPLY, "file"), sort_keys=True) == \
        json.dumps(TEST_DRS_REPLY["access_methods"][0], sort_keys=True)

    assert drs_utils.get_access_method_of_type(TEST_DRS_REPLY_NO_ACCESS, "file") is None
    assert drs_utils.get_access_method_of_type(TEST_DRS_REPLY_NO_ACCESS, "http") is None


def test_drs_uri_decode():
    assert drs_utils.decode_drs_uri("drs://example.org/abc") == "https://example.org/ga4gh/drs/v1/objects/abc"

    with pytest.raises(drs_exceptions.DrsInvalidScheme):
        drs_utils.decode_drs_uri("http://example.org/abc")


@responses.activate
def test_drs_uri_fetch_sync():
    responses.add(responses.GET, f"https://example.org/ga4gh/drs/v1/objects/{TEST_DRS_ID}",
                  json=TEST_DRS_REPLY, status=200)

    assert json.dumps(drs_utils.fetch_drs_record_by_uri(f"drs://example.org/{TEST_DRS_ID}"), sort_keys=True) == \
        json.dumps(TEST_DRS_REPLY, sort_keys=True)


@responses.activate
def test_drs_uri_fetch_sync_errors():
    responses.add(responses.GET, "https://example.org/ga4gh/drs/v1/objects/abc",
                  json=errors.not_found_error(drs_compat=True), status=404)
    responses.add(responses.GET, "https://example.org/ga4gh/drs/v1/objects/xyz",
                  json=errors.not_found_error(drs_compat=True), status=400)

    with pytest.raises(drs_exceptions.DrsRecordNotFound):
        drs_utils.fetch_drs_record_by_uri("drs://example.org/abc")

    with pytest.raises(drs_exceptions.DrsRequestError):
        drs_utils.fetch_drs_record_by_uri("drs://example.org/xyz")


@pytest.fixture
def mocked():
    with aioresponses() as m:
        yield m


@pytest.mark.asyncio
async def test_drs_uri_fetch_async(mocked):
    mocked.get(f"https://example.org/ga4gh/drs/v1/objects/{TEST_DRS_ID}", payload=TEST_DRS_REPLY, status=200)

    assert json.dumps(
        await drs_utils.fetch_drs_record_by_uri_async(f"drs://example.org/{TEST_DRS_ID}"),
        sort_keys=True
    ) == json.dumps(TEST_DRS_REPLY, sort_keys=True)


@pytest.mark.asyncio
async def test_drs_uri_fetch_async_errors(mocked):
    mocked.get("https://example.org/ga4gh/drs/v1/objects/abc",
               payload=errors.not_found_error(drs_compat=True), status=404)
    mocked.get("https://example.org/ga4gh/drs/v1/objects/xyz",
               payload=errors.not_found_error(drs_compat=True), status=400)

    with pytest.raises(drs_exceptions.DrsRecordNotFound):
        await drs_utils.fetch_drs_record_by_uri_async("drs://example.org/abc")

    with pytest.raises(drs_exceptions.DrsRequestError):
        await drs_utils.fetch_drs_record_by_uri_async("drs://example.org/xyz")


def test_drs_resolver_class_basic():
    r = drs_resolver.DrsResolver()

    assert r.decode_drs_uri("drs://example.org/abc") == "https://example.org/ga4gh/drs/v1/objects/abc"

    with pytest.raises(drs_exceptions.DrsInvalidScheme):
        r.decode_drs_uri("http://example.org/abc")


@responses.activate
def test_drs_resolver_class_sync():
    responses.add(responses.GET, f"https://example.org/ga4gh/drs/v1/objects/{TEST_DRS_ID}",
                  json=TEST_DRS_REPLY, status=200)

    r = drs_resolver.DrsResolver(cache_ttl=1.0)

    uri = f"drs://example.org/{TEST_DRS_ID}"
    rec1 = r.fetch_drs_record_by_uri(uri)
    assert uri in r._drs_record_cache
    rec2 = r.fetch_drs_record_by_uri(uri)
    assert rec1 == rec2

    time.sleep(1.1)

    responses.add(responses.GET, f"https://example.org/ga4gh/drs/v1/objects/{TEST_DRS_ID}",
                  json=TEST_DRS_REPLY, status=200)

    r.fetch_drs_record_by_uri(uri)  # should refetch


@pytest.mark.asyncio
async def test_drs_resolver_class_async(mocked):
    r = drs_resolver.DrsResolver()

    mocked.get(f"https://example.org/ga4gh/drs/v1/objects/{TEST_DRS_ID}", payload=TEST_DRS_REPLY, status=200)

    uri = f"drs://example.org/{TEST_DRS_ID}"
    rec1 = await r.fetch_drs_record_by_uri_async(uri)
    assert uri in r._drs_record_cache
    rec2 = await r.fetch_drs_record_by_uri_async(uri)
    assert rec1 == rec2

    time.sleep(1.1)

    await r.fetch_drs_record_by_uri_async(uri)  # should refetch
