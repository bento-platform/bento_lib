import logging
import pytest

from aioresponses import aioresponses
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import Response as HttpxResponse
from pydantic import BaseModel

from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.constants import RESOURCE_EVERYTHING
from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.responses.fastapi_errors import (
    http_exception_handler_factory,
    bento_auth_exception_handler_factory,
    validation_exception_handler_factory,
)

from .common import (
    PERMISSION_INGEST_DATA,
    authz_test_case_params,
    authz_test_cases,
    TEST_AUTHZ_VALID_POST_BODY,
    TEST_AUTHZ_HEADERS,
)


logger = logging.getLogger(__name__)


class TestBody(BaseModel):
    test1: str
    test2: str


class TestTokenBody(BaseModel):
    token: str
    payload: str


# Standard test app -----------------------------------------------------------

test_app = FastAPI()
test_app.exception_handler(HTTPException)(http_exception_handler_factory(logger, None))
test_app.exception_handler(BentoAuthException)(bento_auth_exception_handler_factory(logger, None))
test_app.exception_handler(RequestValidationError)(validation_exception_handler_factory(None))
test_client_ = TestClient(test_app)


@pytest.fixture
def test_client():
    return test_client_


@test_app.get("/get-404")
def get_404():
    raise HTTPException(status_code=404, detail="Hello")


@test_app.get("/get-500")
def get_500():
    raise HTTPException(status_code=500, detail="Hello")


@test_app.post("/post-400")
def post_400(body: TestBody):
    return JSONResponse(body.dict())


@test_app.get("/get-403")
def get_403():
    raise BentoAuthException("Hello", status_code=403)


# Auth test app ---------------------------------------------------------------

test_app_auth = FastAPI()
test_app_auth.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["Authorization"],
    allow_credentials=True,
    allow_methods=["*"],
)
auth_middleware = FastApiAuthMiddleware(bento_authz_service_url="https://bento-auth.local", logger=logger)
auth_middleware.attach(test_app_auth)

test_app_auth.exception_handler(HTTPException)(http_exception_handler_factory(logger, auth_middleware))
test_app_auth.exception_handler(BentoAuthException)(bento_auth_exception_handler_factory(logger, auth_middleware))
test_app_auth.exception_handler(RequestValidationError)(validation_exception_handler_factory(auth_middleware))

fastapi_client_auth_ = TestClient(test_app_auth)


@pytest.fixture
def fastapi_client_auth():
    return fastapi_client_auth_


@test_app_auth.post("/post-public", dependencies=[auth_middleware.dep_public_endpoint()])
def auth_post_public(body: TestBody):
    return JSONResponse(body.dict())


@test_app_auth.post("/post-private", dependencies=[
    auth_middleware.dep_require_permissions_on_resource(frozenset({PERMISSION_INGEST_DATA})),
])
def auth_post_private(body: TestBody):
    return JSONResponse(body.dict())


@test_app_auth.post("/post-private-no-flag", dependencies=[
    auth_middleware.dep_require_permissions_on_resource(frozenset({PERMISSION_INGEST_DATA}), set_authz_flag=False),
])
def auth_post_private_no_flag(request: Request, body: TestBody):
    auth_middleware.mark_authz_done(request)
    return JSONResponse(body.dict())


@test_app_auth.post("/post-private-no-token", dependencies=[
    auth_middleware.dep_require_permissions_on_resource(frozenset({PERMISSION_INGEST_DATA}), require_token=False),
])
def auth_post_private_no_token(body: TestBody):
    return JSONResponse(body.dict())


@test_app_auth.post("/post-missing-authz")
def auth_post_missing_authz(body: TestBody):
    return JSONResponse(body.dict())  # no authz flag set, so will return a 403


@test_app_auth.get("/get-500")
def auth_get_500():
    raise HTTPException(500, "Internal Server Error")


@test_app_auth.post("/post-with-token-in-body")
async def auth_post_with_token_in_body(request: Request, body: TestTokenBody):
    token = body.token
    await auth_middleware.async_check_authz_evaluate(
        request,
        frozenset({PERMISSION_INGEST_DATA}),
        RESOURCE_EVERYTHING,
        require_token=True,
        set_authz_flag=True,
        headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
    )
    return JSONResponse({"payload": body.payload})


# Auth test app (disabled auth middleware) ------------------------------------

test_app_auth_disabled = FastAPI()
auth_middleware_disabled = FastApiAuthMiddleware(
    bento_authz_service_url="https://bento-auth.local",
    logger=logger,
    enabled=False,
)
auth_middleware_disabled.attach(test_app_auth_disabled)

test_app_auth_disabled.exception_handler(HTTPException)(
    http_exception_handler_factory(logger, auth_middleware_disabled))
test_app_auth_disabled.exception_handler(BentoAuthException)(
    bento_auth_exception_handler_factory(logger, auth_middleware_disabled))
test_app_auth_disabled.exception_handler(RequestValidationError)(
    validation_exception_handler_factory(auth_middleware_disabled))

fastapi_client_auth_disabled_ = TestClient(test_app_auth_disabled)


@pytest.fixture
def fastapi_client_auth_disabled():
    return fastapi_client_auth_disabled_


@test_app_auth_disabled.post("/post-public", dependencies=[auth_middleware_disabled.dep_public_endpoint()])
def auth_disabled_post_public(body: TestBody):
    return JSONResponse(body.dict())


@test_app_auth_disabled.post("/post-private", dependencies=[
    auth_middleware_disabled.dep_require_permissions_on_resource(frozenset({PERMISSION_INGEST_DATA})),
])
def auth_disabled_post_private(body: TestBody):
    return JSONResponse(body.dict())

# -----------------------------------------------------------------------------


@pytest.fixture
def aioresponse():
    with aioresponses() as m:
        yield m


def _expect_error(r: HttpxResponse, code: int, msg: str):
    assert r.status_code == code
    data = r.json()
    assert data["code"] == code
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == msg


def test_fastapi_middleware_init_logger():
    inst = FastApiAuthMiddleware(bento_authz_service_url="https://bento-auth.local")
    inst._log_error("doesn't appear")
    inst.attach(FastAPI())  # should create a logger if not specified
    inst._log_error("does appear")
    assert inst._logger is not None


def test_fastapi_http_exception_404(test_client: TestClient):
    _expect_error(test_client.get("/get-404"), 404, "Hello")


def test_fastapi_http_exception_500(test_client: TestClient):
    _expect_error(test_client.get("/get-500"), 500, "Hello")


def test_fastapi_auth_exception_403(test_client: TestClient):
    _expect_error(test_client.get("/get-403"), 403, "Hello")


def test_fastapi_validation_exception(test_client: TestClient):
    _expect_error(test_client.post("/post-400", json={"test2": 5}), 400, "body.test1: field required")
    _expect_error(
        test_client.post("/post-400", json={"test1": "a", "test2": {"a": "b"}}), 400, "body.test2: str type expected")


def test_fastapi_auth_public(fastapi_client_auth: TestClient):
    r = fastapi_client_auth.post("/post-public", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200


@pytest.mark.parametrize(authz_test_case_params, authz_test_cases)
def test_fastapi_auth(
    # case variables
    authz_code: int,
    authz_res: bool,
    test_url: str,
    inc_headers: bool,
    test_code: int,
    # fixtures
    aioresponse: aioresponses,
    fastapi_client_auth: TestClient,
):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=authz_code, payload={"result": authz_res})
    r = fastapi_client_auth.post(
        test_url, headers=(TEST_AUTHZ_HEADERS if inc_headers else {}), json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == test_code


def test_fastapi_auth_invalid_body(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": True})
    r = fastapi_client_auth.post("/post-private", headers=TEST_AUTHZ_HEADERS, json={"test1": "a"})
    assert r.status_code == 400


def test_fastapi_auth_500(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": True})
    r = fastapi_client_auth.get("/get-500", headers=TEST_AUTHZ_HEADERS)
    assert r.status_code == 500


def test_fastapi_auth_missing_token(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    # forbidden - no token
    r = fastapi_client_auth.post("/post-private", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 401


def test_fastapi_auth_options_call(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    # allow OPTIONS through
    r = fastapi_client_auth.options("/post-private", headers={
        "Origin": "http://localhost",
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 200


def test_fastapi_auth_post_with_token_in_body(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": True})
    r = fastapi_client_auth.post("/post-with-token-in-body", json={"token": "test", "payload": "hello world"})
    assert r.status_code == 200
    assert r.text == '{"payload":"hello world"}'


@pytest.mark.asyncio
async def test_fastapi_auth_disabled(aioresponse: aioresponses, fastapi_client_auth_disabled: TestClient):
    # middleware is disabled, should work anyway
    r = fastapi_client_auth_disabled.post("/post-public", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200

    # middleware is disabled, should allow through
    r = fastapi_client_auth_disabled.post("/post-private", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200

    assert await auth_middleware_disabled.async_check_authz_evaluate(
        Request({"type": "http"}),
        frozenset({PERMISSION_INGEST_DATA}),
        {"everything": True},
    ) is None
