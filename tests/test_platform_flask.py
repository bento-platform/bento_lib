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

    @application.route("/test3", methods=["GET", "POST"])
    @fd.flask_permissions({"POST": {"owner"}})
    def test3():
        return "test3"

    with application.test_client() as client:
        yield client


def test_flask_forbidden_error(flask_client):
    # Turn CHORD permissions mode on to make sure we're getting real permissions checks
    fd.CHORD_PERMISSIONS = True

    # /test1

    r = flask_client.get("/test1")
    assert r.status_code == 403
    assert r.get_json()["code"] == 403

    r = flask_client.get("/test1", headers={"X-User": "test", "X-User-Role": "user"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test1"

    r = flask_client.get("/test1", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test1"

    # /test2

    r = flask_client.get("/test2")
    assert r.status_code == 403
    assert r.get_json()["code"] == 403

    r = flask_client.get("/test2", headers={"X-User": "test", "X-User-Role": "user"})
    assert r.status_code == 403
    assert r.get_json()["code"] == 403

    r = flask_client.get("/test2", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test2"

    # /test3

    r = flask_client.get("/test3")
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test3"

    r = flask_client.post("/test3")
    assert r.status_code == 403
    assert r.get_json()["code"] == 403

    r = flask_client.get("/test3", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "test3"
