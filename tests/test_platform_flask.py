import bento_lib.auth.flask_decorators as fd
import bento_lib.responses.flask_errors as fe
import logging
import pytest

from flask import Flask
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError


@pytest.fixture
def flask_client():
    application = Flask(__name__)

    application.register_error_handler(Exception, fe.flask_error_wrap_with_traceback(fe.flask_internal_server_error))
    application.register_error_handler(
        InternalServerError,
        fe.flask_error_wrap_with_traceback(fe.flask_internal_server_error, logger=logging.getLogger(__name__)))
    application.register_error_handler(BadRequest, fe.flask_error_wrap(fe.flask_bad_request_error))
    application.register_error_handler(NotFound, fe.flask_error_wrap(fe.flask_not_found_error, drs_compat=True))

    @application.route("/500")
    def r500():
        raise Exception("help")

    @application.route("/test0")
    def test0():
        raise InternalServerError("test0")

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


def test_flask_errors(flask_client):
    # Turn CHORD permissions mode on to make sure we're getting real permissions checks
    fd.BENTO_PERMISSIONS = True

    # non-existent endpoint

    r = flask_client.get("/non-existent")
    assert r.status_code == 404
    rj = r.get_json()
    assert rj["code"] == 404

    # - We passed drs_compat=True to this, so check for DRS-specific fields
    assert rj["status_code"] == rj["code"]
    assert rj["msg"] == rj["message"]

    # server error endpoint

    r = flask_client.get("/500")
    assert r.status_code == 500
    assert r.get_json()["code"] == 500

    # /test0

    r = flask_client.get("/test0")
    assert r.status_code == 500
    assert r.get_json()["code"] == 500
    assert r.get_json()["errors"][0]["message"] == "500 Internal Server Error: test0"

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
