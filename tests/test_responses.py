import chord_lib.responses as responses
from dateutil.parser import isoparse


def test_errors():
    e = responses.errors.forbidden_error()
    assert len(list(e.keys())) == 3
    assert "code" in e and "message" in e and "timestamp" in e
    assert e["code"] == 403
    assert e["message"] == "Forbidden"
    assert isoparse(e["timestamp"])
