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

from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.responses.fastapi_errors import (
    http_exception_handler_factory,
    validation_exception_handler,
)


logger = logging.getLogger(__name__)


# Standard test app -----------------------------------------------------------

test_app = FastAPI()
test_app.exception_handler(HTTPException)(http_exception_handler_factory(logger))
test_app.exception_handler(RequestValidationError)(validation_exception_handler)
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


class TestBody(BaseModel):
    test1: str
    test2: str


@test_app.post("/post-400")
def post_400(body: TestBody):
    return JSONResponse(body.dict())


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
test_client_auth_ = TestClient(test_app_auth)


@pytest.fixture
def test_client_auth():
    return test_client_auth_


class TestBody(BaseModel):
    test1: str
    test2: str


@test_app_auth.post("/post-public", dependencies=[auth_middleware.dep_public_endpoint()])
def auth_post_pulic(body: TestBody):
    return JSONResponse(body.dict())


PERMISSION_INGEST_DATA = "ingest:data"


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


# Auth test app (disabled auth middleware) ------------------------------------

test_app_auth_disabled = FastAPI()
auth_middleware_disabled = FastApiAuthMiddleware(
    bento_authz_service_url="https://bento-auth.local",
    logger=logger,
    enabled=False,
)
auth_middleware_disabled.attach(test_app_auth_disabled)
test_client_auth_disabled_ = TestClient(test_app_auth_disabled)


@pytest.fixture
def test_client_auth_disabled():
    return test_client_auth_disabled_


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


TEST_VALID_POST_BODY = {"test1": "a", "test2": "b"}
TEST_AUTHZ_HEADERS = {"Authorization": "Bearer test"}


def test_fastapi_http_exception_404(test_client: TestClient):
    _expect_error(test_client.get("/get-404"), 404, "Hello")


def test_fastapi_http_exception_500(test_client: TestClient):
    _expect_error(test_client.get("/get-500"), 500, "Hello")


def test_fastapi_validation_exception(test_client: TestClient):
    _expect_error(test_client.post("/post-400", json={"test2": 5}), 400, "body.test1: field required")
    _expect_error(
        test_client.post("/post-400", json={"test1": "a", "test2": {"a": "b"}}), 400, "body.test2: str type expected")


def test_fastapi_auth_public(test_client_auth: TestClient):
    r = test_client_auth.post("/post-public", json=TEST_VALID_POST_BODY)
    assert r.status_code == 200


# cases: (authz response code, authz response result, test client URL, auth header included, assert final response)
@pytest.mark.parametrize("authz_code, authz_res, test_url, inc_headers, test_code", (
    # allowed through
    (200, True, "/post-private", True, 200),
    (200, True, "/post-private-no-flag", True, 200),
    # forbidden
    (200, False, "/post-private", True, 403),
    # error from auth service
    (500, False, "/post-private", True, 500),
    # allowed - no token
    (200, True, "/post-private-no-token", False, 200),
    # allowed - no token required, but one given
    (200, True, "/post-private-no-token", True, 200),
    # missing authz flag set
    (200, True, "/post-missing-authz", True, 403),
))
def test_fastapi_auth_private(
    # case variables
    authz_code: int,
    authz_res: bool,
    test_url: str,
    inc_headers: bool,
    test_code: int,
    # fixtures
    aioresponse: aioresponses,
    test_client_auth: TestClient,
):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=authz_code, payload={"result": authz_res})
    r = test_client_auth.post(test_url, headers=(TEST_AUTHZ_HEADERS if inc_headers else {}), json=TEST_VALID_POST_BODY)
    assert r.status_code == test_code


def test_fastapi_auth_missing_token(aioresponse: aioresponses, test_client_auth: TestClient):
    # forbidden - no token
    r = test_client_auth.post("/post-private", json=TEST_VALID_POST_BODY)
    assert r.status_code == 401


def test_fastapi_auth_options_call(aioresponse: aioresponses, test_client_auth: TestClient):
    # allow OPTIONS through
    r = test_client_auth.options("/post-private", headers={
        "Origin": "http://localhost",
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_fastapi_auth_disabled(aioresponse: aioresponses, test_client_auth_disabled: TestClient):
    # middleware is disabled, should allow through
    r = test_client_auth_disabled.post("/post-private", json=TEST_VALID_POST_BODY)
    assert r.status_code == 200

    assert await auth_middleware_disabled.async_check_authz_evaluate(
        Request({"type": "http"}),
        frozenset({PERMISSION_INGEST_DATA}),
        {"everything": True},
    ) is None
