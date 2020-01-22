import chord_lib.responses as responses
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
