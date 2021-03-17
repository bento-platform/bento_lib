import json

from bento_lib.drs import utils as drs_utils


TEST_DRS_REPLY_NO_ACCESS = {
    "checksums": [{
        "checksum": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        "type": "sha-256",
    }],
    "created_time": "",  # TODO: RFC3339
    "updated_time": "",  # TODO: RFC3339
    "id": "dd11912c-3433-4a0a-8a01-3c0699288bef",
    "mime_type": "text/plain",
    "self_uri": "drs://localhost/dd11912c-3433-4a0a-8a01-3c0699288bef",
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


def test_drs_uri_decode():
    assert drs_utils.decode_drs_uri("drs://example.org/abc") == "https://example.org/ga4gh/drs/v1/objects/abc"
    assert drs_utils.decode_drs_uri("drs://example.org/abc", internal_drs_base_url="http://localhost/sub/") == \
           "http://localhost/sub/ga4gh/drs/v1/objects/abc"
    # TODO: Really, Bento should pass ga4gh/drs URLs to DRS directly instead of under a sub-path


def test_drs_uri_fetch():
    pass
