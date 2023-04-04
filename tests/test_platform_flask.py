import bento_lib.auth.flask_decorators as fd
import bento_lib.responses.flask_errors as fe

from bento_lib.auth.middleware import AuthxFlaskMiddleware, AuthXException
from bento_lib.auth.wrappers import authn_token_optional_flask_wrapper, authn_token_required_flask_wrapper

import logging
import pytest

from flask import Flask, current_app
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError


@pytest.fixture
def flask_client():
    application = Flask(__name__)

    application.register_error_handler(AuthXException, fe.flask_error_wrap(fe.flask_unauthorized_error))
    application.register_error_handler(Exception, fe.flask_error_wrap_with_traceback(fe.flask_internal_server_error))
    application.register_error_handler(
        InternalServerError,
        fe.flask_error_wrap_with_traceback(fe.flask_internal_server_error, logger=logging.getLogger(__name__)))
    application.register_error_handler(BadRequest, fe.flask_error_wrap(fe.flask_bad_request_error))
    application.register_error_handler(NotFound, fe.flask_error_wrap(fe.flask_not_found_error, drs_compat=True))

    with application.app_context():
        # enable authx middleware
        authxm = AuthxFlaskMiddleware(oidc_iss="https://auth.qa.bento.c3g.calculquebec.ca/auth/realms/bentov2",
                                      oidc_wellknown_path=("""https://auth.qa.bento.c3g.calculquebec.ca"""
                                                           """/auth/realms/bentov2/protocol/openid-connect/certs"""),
                                      client_id="local_bentov2")  # using default
        current_app.authx = {}
        current_app.authx['enabled'] = True
        current_app.authx['middleware'] = authxm

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

    @application.route("/authn/test1")
    @authn_token_optional_flask_wrapper
    def authn_test1():
        return "authn-test1"

    @application.route("/authn/test2")
    @authn_token_required_flask_wrapper
    def authn_test2():
        return "authn-test2"

    with application.test_client() as client:
        yield client


@pytest.fixture
def flask_client2():
    application = Flask(__name__)

    application.register_error_handler(AuthXException, fe.flask_error_wrap(fe.flask_unauthorized_error))
    application.register_error_handler(Exception, fe.flask_error_wrap_with_traceback(fe.flask_internal_server_error))
    application.register_error_handler(BadRequest, fe.flask_error_wrap(fe.flask_bad_request_error))
    application.register_error_handler(NotFound, fe.flask_error_wrap(fe.flask_not_found_error, drs_compat=True))

    with application.app_context():
        # disable authx middleware
        authxm = None
        current_app.authx = {}
        current_app.authx['enabled'] = False
        current_app.authx['middleware'] = authxm

    @application.route("/authn/test3")
    @authn_token_optional_flask_wrapper
    def authn_test3():
        return "authn-test3"

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


def test_flask_errors2(flask_client2):
    # /authn/test3

    # - test disabled authx endpoint
    r = flask_client2.get("/authn/test3")
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "authn-test3"
