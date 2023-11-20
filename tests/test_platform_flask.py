import bento_lib.responses.flask_errors as fe

import logging
import pytest
import responses

from flask import Flask, jsonify, Request, request
from flask.testing import FlaskClient
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

from bento_lib.auth.middleware.flask import FlaskAuthMiddleware
from bento_lib.auth.permissions import P_INGEST_DATA
from bento_lib.auth.resources import RESOURCE_EVERYTHING

from .common import (
    authz_test_case_params,
    authz_test_cases,
    TEST_AUTHZ_VALID_POST_BODY,
    TEST_AUTHZ_HEADERS,
)


logger = logging.getLogger(__name__)


# Standard test app -----------------------------------------------------------


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
    def test1():
        return {"hello": "test1"}

    with application.test_client() as client:
        yield client


# Auth test app ---------------------------------------------------------------


@pytest.fixture
def flask_client_auth():
    test_app_auth = Flask(__name__)
    auth_middleware = FlaskAuthMiddleware(bento_authz_service_url="https://bento-auth.local", logger=logger)
    auth_middleware.attach(test_app_auth)

    test_app_auth.register_error_handler(
        Exception, fe.flask_error_wrap_with_traceback(fe.flask_internal_server_error, authz=auth_middleware))
    test_app_auth.register_error_handler(
        NotFound, fe.flask_error_wrap(fe.flask_not_found_error, drs_compat=True, authz=auth_middleware))

    @test_app_auth.route("/post-public", methods=["POST"])
    @auth_middleware.deco_public_endpoint
    def auth_post_public():
        return jsonify(request.json)

    @test_app_auth.route("/post-private", methods=["POST"])
    @auth_middleware.deco_require_permissions_on_resource(frozenset({P_INGEST_DATA}))
    def auth_post_private():
        return jsonify(request.json)

    @test_app_auth.route("/post-private-no-flag", methods=["POST"])
    @auth_middleware.deco_require_permissions_on_resource(frozenset({P_INGEST_DATA}), set_authz_flag=False)
    def auth_post_private_no_flag():
        auth_middleware.mark_authz_done(request)
        return jsonify(request.json)

    @test_app_auth.route("/post-private-no-token", methods=["POST"])
    @auth_middleware.deco_require_permissions_on_resource(frozenset({P_INGEST_DATA}), require_token=False)
    def auth_post_private_no_token():
        return jsonify(request.json)

    @test_app_auth.route("/post-missing-authz", methods=["POST"])
    def auth_post_missing_authz():
        return jsonify(request.json)  # no authz flag set, so will return a 403

    @test_app_auth.route("/get-500", methods=["GET"])
    def auth_500():
        raise Exception("aaa")

    @test_app_auth.route("/get-404", methods=["GET"])
    def auth_404():
        raise NotFound()

    @test_app_auth.route("/post-with-token-in-body", methods=["POST"])
    def auth_post_with_token_in_body():
        token = request.json["token"]
        payload = request.json["payload"]
        auth_middleware.check_authz_evaluate(
            request,
            frozenset({P_INGEST_DATA}),
            RESOURCE_EVERYTHING,
            require_token=True,
            set_authz_flag=True,
            headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
        )
        return jsonify({"payload": payload})

    @test_app_auth.route("/post-with-token-evaluate-one", methods=["POST"])
    def auth_post_with_token_evaluate_one():
        token = request.json["token"]

        auth_middleware.mark_authz_done(request)
        return jsonify({"payload": auth_middleware.evaluate_one(
            request,
            RESOURCE_EVERYTHING,
            P_INGEST_DATA,
            require_token=True,
            headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
        )})

    @test_app_auth.route("/post-with-token-evaluate-to-dict", methods=["POST"])
    def auth_post_with_token_evaluate__to_dict():
        token = request.json["token"]

        auth_middleware.mark_authz_done(request)
        return jsonify({"payload": auth_middleware.evaluate_to_dict(
            request,
            (RESOURCE_EVERYTHING,),
            (P_INGEST_DATA,),
            require_token=True,
            headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
        )})

    with test_app_auth.test_client() as client:
        yield client


# Auth test app (disabled auth middleware) ------------------------------------


@pytest.fixture
def flask_client_auth_disabled_with_middleware():
    test_app_auth_disabled = Flask(__name__)
    auth_middleware_disabled = FlaskAuthMiddleware(
        bento_authz_service_url="https://bento-auth.local",
        logger=logger,
        enabled=False,
    )
    auth_middleware_disabled.attach(test_app_auth_disabled)

    @test_app_auth_disabled.route("/post-public", methods=["POST"])
    @auth_middleware_disabled.deco_public_endpoint
    def auth_disabled_post_public():
        return jsonify(request.json)

    @test_app_auth_disabled.route("/post-private", methods=["POST"])
    @auth_middleware_disabled.deco_require_permissions_on_resource(frozenset({P_INGEST_DATA}))
    def auth_disabled_post_private():
        return jsonify(request.json)

    with test_app_auth_disabled.test_client() as client:
        yield client, auth_middleware_disabled


# -----------------------------------------------------------------------------


def test_flask_middleware_init_logger():
    inst = FlaskAuthMiddleware(bento_authz_service_url="https://bento-auth.local")
    app = Flask(__name__)
    inst.attach(app)
    assert inst._logger == app.logger


def test_flask_errors(flask_client):
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
    assert r.status_code == 200
    assert r.get_json()["hello"] == "test1"


def test_flask_auth_public(flask_client_auth: FlaskClient):
    r = flask_client_auth.post("/post-public", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200


@pytest.mark.parametrize(authz_test_case_params, authz_test_cases)
@responses.activate
def test_flask_auth(
    # case variables
    authz_code: int,
    authz_res: bool,
    test_url: str,
    inc_headers: bool,
    test_code: int,
    # fixtures
    flask_client_auth: FlaskClient,
):
    responses.add(
        responses.POST,
        "https://bento-auth.local/policy/evaluate",
        json={"result": [[authz_res]]},
        status=authz_code,
    )
    r = flask_client_auth.post(
        test_url, headers=(TEST_AUTHZ_HEADERS if inc_headers else {}), json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == test_code


@responses.activate
def test_flask_auth_500(flask_client_auth: FlaskClient):
    responses.add(responses.POST, "https://bento-auth.local/policy/evaluate", json={"result": [[True]]}, status=200)
    r = flask_client_auth.get("/get-500", headers=TEST_AUTHZ_HEADERS)
    assert r.status_code == 500


@responses.activate
def test_flask_auth_404(flask_client_auth: FlaskClient):
    responses.add(responses.POST, "https://bento-auth.local/policy/evaluate", json={"result": [[True]]}, status=200)
    r = flask_client_auth.get("/get-404", headers=TEST_AUTHZ_HEADERS)
    assert r.status_code == 404


@responses.activate
def test_flask_auth_post_with_token_in_body(flask_client_auth: FlaskClient):
    responses.add(responses.POST, "https://bento-auth.local/policy/evaluate", json={"result": [[True]]}, status=200)
    r = flask_client_auth.post("/post-with-token-in-body", json={"token": "test", "payload": "hello world"})
    assert r.status_code == 200
    assert r.text == '{"payload":"hello world"}\n'


@responses.activate
def test_flask_auth_post_with_token_evaluate_one(flask_client_auth: FlaskClient):
    responses.add(responses.POST, "https://bento-auth.local/policy/evaluate", json={"result": [[True]]}, status=200)
    r = flask_client_auth.post("/post-with-token-evaluate-one", json={"token": "test"})
    assert r.status_code == 200
    assert r.text == '{"payload":true}\n'


@responses.activate
def test_flask_auth_post_with_token_evaluate_to_dict(flask_client_auth: FlaskClient):
    responses.add(responses.POST, "https://bento-auth.local/policy/evaluate", json={"result": [[True]]}, status=200)
    r = flask_client_auth.post("/post-with-token-evaluate-to-dict", json={"token": "test"})
    assert r.status_code == 200
    assert r.text == '{"payload":[{"ingest:data":true}]}\n'


@responses.activate
def test_flask_auth_disabled(flask_client_auth_disabled_with_middleware: tuple[FlaskClient, FlaskAuthMiddleware]):
    flask_client_auth_disabled, auth_middleware_disabled = flask_client_auth_disabled_with_middleware

    # middleware is disabled, should work anyway
    r = flask_client_auth_disabled.post("/post-public", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200

    # middleware is disabled, should allow through
    r = flask_client_auth_disabled.post("/post-private", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200

    assert auth_middleware_disabled.check_authz_evaluate(
        Request({}),
        frozenset({P_INGEST_DATA}),
        {"everything": True},
    ) is None
