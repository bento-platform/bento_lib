import json
import pytest
import requests_mock

from bento_lib.responses import errors
from bento_lib.drs import utils as drs_utils

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


def test_get_file_access_method():
    assert json.dumps(drs_utils.get_file_access_method_if_any(TEST_DRS_REPLY), sort_keys=True) == \
        json.dumps(TEST_DRS_REPLY["access_methods"][0], sort_keys=True)

    assert drs_utils.get_file_access_method_if_any(TEST_DRS_REPLY_NO_ACCESS) is None


def test_drs_uri_decode():
    assert drs_utils.decode_drs_uri("drs://example.org/abc") == "https://example.org/ga4gh/drs/v1/objects/abc"
    assert drs_utils.decode_drs_uri("drs://example.org/abc", internal_drs_base_url="http://localhost/sub/") == \
           "http://localhost/sub/ga4gh/drs/v1/objects/abc"

    with pytest.raises(drs_utils.DrsInvalidScheme):
        drs_utils.decode_drs_uri("http://example.org/abc")

    # TODO: Really, Bento should pass ga4gh/drs URLs to DRS directly instead of under a sub-path


def test_drs_uri_fetch():
    with requests_mock.Mocker() as m:
        m.get(f"https://example.org/ga4gh/drs/v1/objects/{TEST_DRS_ID}", json=TEST_DRS_REPLY)
        m.get(f"http://localhost/ga4gh/drs/v1/objects/{TEST_DRS_ID}", json=TEST_DRS_REPLY)

        m.get("https://example.org/ga4gh/drs/v1/objects/abc", status_code=404, json=errors.not_found_error())
        m.get("http://localhost/ga4gh/drs/v1/objects/abc", status_code=404, json=errors.not_found_error())

        assert json.dumps(drs_utils.fetch_drs_record_by_uri(f"drs://example.org/{TEST_DRS_ID}"), sort_keys=True) == \
            json.dumps(TEST_DRS_REPLY, sort_keys=True)
        assert json.dumps(drs_utils.fetch_drs_record_by_uri(
            f"drs://example.org/{TEST_DRS_ID}",
            internal_drs_base_url="http://localhost/"
        ), sort_keys=True) == json.dumps(TEST_DRS_REPLY, sort_keys=True)

        with pytest.raises(drs_utils.DrsRequestError):
            drs_utils.fetch_drs_record_by_uri("drs://example.org/abc")

        with pytest.raises(drs_utils.DrsRequestError):
            drs_utils.fetch_drs_record_by_uri("drs://example.org/abc", internal_drs_base_url="http://localhost/")
