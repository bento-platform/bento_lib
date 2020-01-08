import chord_lib.auth.flask_decorators as fd
import pytest

from flask import Flask


@pytest.fixture
def flask_client():
    application = Flask(__name__)

    @application.route("/test1")
    @fd.flask_permissions_any_user
    def test1():
        return "test1"

    @application.route("/test2")
    @fd.flask_permissions_owner
    def test2():
        return "test2"

    with application.test_client() as client:
        yield client


def test_flask_forbidden_error(flask_client):
    # Turn debug mode off to make sure we're getting real permissions checks
    fd.CHORD_DEBUG = False

    r = flask_client.get("/test1")
    assert r.status_code == 403
    data = r.get_json()
    assert data["code"] == 403

    r = flask_client.get("/test1", headers={"X-User": "test", "X-User-Role": "user"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test1"

    r = flask_client.get("/test1", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test1"

    r = flask_client.get("/test2")
    assert r.status_code == 403
    data = r.get_json()
    assert data["code"] == 403

    r = flask_client.get("/test2", headers={"X-User": "test", "X-User-Role": "user"})
    assert r.status_code == 403
    data = r.get_json()
    assert data["code"] == 403

    r = flask_client.get("/test2", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test2"
