import bento_lib.responses as responses
import json
from dateutil.parser import isoparse


def test_errors():
    e = responses.errors.http_error(900)
    assert e["code"] == 500  # Internal server error
    assert len(e["errors"]) == 1

    e = responses.errors.http_error(200, "test")
    assert e["code"] == 500  # Internal server error
    assert len(e["errors"]) == 2

    e = responses.errors.forbidden_error()
    assert len(list(e.keys())) == 3
    assert "code" in e and "message" in e and "timestamp" in e
    assert e["code"] == 403
    assert e["message"] == "Forbidden"
    assert isoparse(e["timestamp"])

    e = responses.errors.forbidden_error("test message")
    assert len(list(e.keys())) == 4
    assert "code" in e and "message" in e and "timestamp" in e and "errors" in e
    assert e["code"] == 403
    assert e["message"] == "Forbidden"
    assert json.dumps(e["errors"]) == '[{"message": "test message"}]'
    assert isoparse(e["timestamp"])

    e = responses.errors.not_found_error("test message", "test message 2")
    assert len(list(e.keys())) == 4
    assert "code" in e and "message" in e and "timestamp" in e and "errors" in e
    assert e["code"] == 404
    assert e["message"] == "Not Found"
    assert json.dumps(e["errors"]) == '[{"message": "test message"}, {"message": "test message 2"}]'
    assert isoparse(e["timestamp"])

    # Test compatibility modes (the base stuff already works, from passing the above tests)

    # DRS
    e = responses.errors.forbidden_error("test message", drs_compat=True)
    assert len(list(e.keys())) == 6
    assert e["status_code"] == 403
    assert e["msg"] == "Forbidden"

    # service registry
    e = responses.errors.forbidden_error("test message", sr_compat=True)
    assert len(list(e.keys())) == 7
    assert e["status"] == 403
    assert e["title"] == "Forbidden"
    assert e["detail"] == "test message"

    # ew
    e = responses.errors.forbidden_error("test message", drs_compat=True, sr_compat=True)
    assert len(list(e.keys())) == 9
    assert e["status"] == 403
    assert e["status_code"] == 403
    assert e["msg"] == "Forbidden"
    assert e["title"] == "Forbidden"
    assert e["detail"] == "test message"

    # beacon
    e = responses.errors.forbidden_error("test message", beacon_meta_callback=lambda: {})
    assert len(list(e.keys())) == 6
    assert e["error"]["errorCode"] == 403
    assert e["error"]["errorMessage"] == "test message"
