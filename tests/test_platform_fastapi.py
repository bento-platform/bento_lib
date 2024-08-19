import logging
import pytest

from aioresponses import aioresponses
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import Response as HttpxResponse
from pydantic import BaseModel

from bento_lib.apps.fastapi import BentoFastAPI
from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.auth.permissions import P_INGEST_DATA
from bento_lib.auth.resources import RESOURCE_EVERYTHING
from bento_lib.config.pydantic import BentoFastAPIBaseConfig
from bento_lib.responses.fastapi_errors import (
    http_exception_handler_factory,
    bento_auth_exception_handler_factory,
    validation_exception_handler_factory,
)
from bento_lib.service_info.helpers import build_bento_service_type
from bento_lib.workflows.workflow_set import WorkflowSet
from bento_lib.workflows.fastapi import build_workflow_router

from .common import (
    authz_test_include_patterns,
    authz_test_exempt_patterns,
    authz_test_case_params,
    authz_test_cases,
    TEST_AUTHZ_VALID_POST_BODY,
    TEST_AUTHZ_HEADERS,
    WDL_DIR,
    WORKFLOW_DEF,
)


logger = logging.getLogger(__name__)

TEST_APP_VERSION = "0.1.0"
TEST_APP_SERVICE_TYPE = build_bento_service_type("test", TEST_APP_VERSION)


class TestBody(BaseModel):
    __test__ = False
    test1: str
    test2: str


class TestTokenPayloadBody(BaseModel):
    __test__ = False
    token: str
    payload: str


class TestTokenBody(BaseModel):
    __test__ = False
    token: str


# Standard test app -----------------------------------------------------------

app_config_test = BentoFastAPIBaseConfig(
    service_id="test",
    service_name="Test App",
    bento_authz_service_url="https://bento-auth.local",
    cors_origins=("*",),
)
app_test = BentoFastAPI(None, app_config_test, logger, {}, TEST_APP_SERVICE_TYPE, TEST_APP_VERSION)
client_test = TestClient(app_test)


@pytest.fixture
def test_client():
    return client_test


@app_test.get("/get-404")
def get_404():
    raise HTTPException(status_code=404, detail="Hello")


@app_test.get("/get-500")
def get_500():
    raise HTTPException(status_code=500, detail="Hello")


@app_test.post("/post-400")
def post_400(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


@app_test.get("/get-403")
def get_403():
    raise BentoAuthException("Hello", status_code=403)


# Auth test app ---------------------------------------------------------------

app_test_auth_config = BentoFastAPIBaseConfig(
    service_id="auth_test",
    service_name="Auth Test",
    bento_authz_service_url="https://bento-auth.local",
    cors_origins=("*",),
)
auth_middleware = FastApiAuthMiddleware.build_from_fastapi_pydantic_config(
    app_test_auth_config,
    logger,
    include_request_patterns=authz_test_include_patterns,
    exempt_request_patterns=authz_test_exempt_patterns,
)
app_test_auth = BentoFastAPI(auth_middleware, app_test_auth_config, logger, {}, TEST_APP_SERVICE_TYPE,
                             TEST_APP_VERSION)

auth_middleware.attach(app_test_auth)

workflow_set = WorkflowSet(WDL_DIR)
workflow_set.add_workflow("test", WORKFLOW_DEF)

app_test_auth.include_router(build_workflow_router(auth_middleware, workflow_set))

fastapi_client_auth_ = TestClient(app_test_auth)


@pytest.fixture
def fastapi_client_auth():
    return fastapi_client_auth_


@app_test_auth.post("/post-exempted")
def auth_post_exempted(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


@app_test_auth.post("/post-public", dependencies=[auth_middleware.dep_public_endpoint()])
def auth_post_public(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


@app_test_auth.post("/post-private", dependencies=[
    auth_middleware.dep_require_permissions_on_resource(frozenset({P_INGEST_DATA})),
])
def auth_post_private(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


@app_test_auth.post("/post-private-no-flag", dependencies=[
    auth_middleware.dep_require_permissions_on_resource(frozenset({P_INGEST_DATA}), set_authz_flag=False),
])
def auth_post_private_no_flag(request: Request, body: TestBody):
    auth_middleware.mark_authz_done(request)
    return JSONResponse(body.model_dump(mode="json"))


@app_test_auth.post("/post-private-no-token", dependencies=[
    auth_middleware.dep_require_permissions_on_resource(frozenset({P_INGEST_DATA}), require_token=False),
])
def auth_post_private_no_token(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


@app_test_auth.post("/post-missing-authz")
def auth_post_missing_authz(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))  # no authz flag set, so will return a 403


@app_test_auth.get("/get-500")
def auth_get_500():
    raise HTTPException(500, "Internal Server Error")


@app_test_auth.post("/post-with-token-in-body")
async def auth_post_with_token_in_body(request: Request, body: TestTokenPayloadBody):
    token = body.token
    await auth_middleware.async_check_authz_evaluate(
        request,
        frozenset({P_INGEST_DATA}),
        RESOURCE_EVERYTHING,
        require_token=True,
        set_authz_flag=True,
        headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
    )
    return JSONResponse({"payload": body.payload})


@app_test_auth.post("/post-with-token-evaluate-one")
async def auth_post_with_token_evaluate_one(request: Request, body: TestTokenBody):
    token = body.token

    auth_middleware.mark_authz_done(request)
    return JSONResponse({"payload": await auth_middleware.async_evaluate_one(
        request,
        RESOURCE_EVERYTHING,
        P_INGEST_DATA,
        require_token=True,
        headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
    )})


@app_test_auth.post("/post-with-token-evaluate-to-dict")
async def auth_post_with_token_evaluate_to_dict(request: Request, body: TestTokenBody):
    token = body.token

    auth_middleware.mark_authz_done(request)
    return JSONResponse({"payload": await auth_middleware.async_evaluate_to_dict(
        request,
        (RESOURCE_EVERYTHING,),
        (P_INGEST_DATA,),
        require_token=True,
        headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
    )})


@app_test_auth.put("/put-test")
async def auth_put_not_included(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


# Auth test app (disabled auth middleware) ------------------------------------

app_test_auth_disabled = FastAPI()
auth_middleware_disabled = FastApiAuthMiddleware(
    bento_authz_service_url="https://bento-auth.local",
    logger=logger,
    enabled=False,
)
auth_middleware_disabled.attach(app_test_auth_disabled)

app_test_auth_disabled.exception_handler(HTTPException)(
    http_exception_handler_factory(logger, auth_middleware_disabled))
app_test_auth_disabled.exception_handler(BentoAuthException)(
    bento_auth_exception_handler_factory(logger, auth_middleware_disabled))
app_test_auth_disabled.exception_handler(RequestValidationError)(
    validation_exception_handler_factory(auth_middleware_disabled))

fastapi_client_auth_disabled_ = TestClient(app_test_auth_disabled)


@pytest.fixture
def fastapi_client_auth_disabled():
    return fastapi_client_auth_disabled_


@app_test_auth_disabled.post("/post-public", dependencies=[auth_middleware_disabled.dep_public_endpoint()])
def auth_disabled_post_public(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))


@app_test_auth_disabled.post("/post-private", dependencies=[
    auth_middleware_disabled.dep_require_permissions_on_resource(frozenset({P_INGEST_DATA})),
])
def auth_disabled_post_private(body: TestBody):
    return JSONResponse(body.model_dump(mode="json"))

# -----------------------------------------------------------------------------


@pytest.fixture
def aioresponse():
    with aioresponses() as m:
        yield m


def _expect_error(r: HttpxResponse, code: int, msgs: tuple[str, ...]):
    assert r.status_code == code
    data = r.json()
    assert data["code"] == code
    assert len(data["errors"]) == len(msgs)

    act_msgs = []
    for err in data["errors"]:
        act_msgs.append(err["message"])

    assert tuple(act_msgs) == msgs


def test_fastapi_auth_middleware_from_config():
    assert isinstance(auth_middleware, FastApiAuthMiddleware)

    assert auth_middleware._bento_authz_service_url == app_test_auth_config.bento_authz_service_url
    assert auth_middleware._enabled
    assert auth_middleware._logger == logger


def test_fastapi_middleware_init_logger():
    inst = FastApiAuthMiddleware(bento_authz_service_url="https://bento-auth.local")
    inst._log_error("doesn't appear")
    inst.attach(FastAPI())  # should create a logger if not specified
    inst._log_error("does appear")
    assert inst._logger is not None


def test_fastapi_http_exception_404(test_client: TestClient):
    _expect_error(test_client.get("/get-404"), 404, ("Hello",))


def test_fastapi_http_exception_500(test_client: TestClient):
    _expect_error(test_client.get("/get-500"), 500, ("Hello",))


def test_fastapi_auth_exception_403(test_client: TestClient):
    _expect_error(test_client.get("/get-403"), 403, ("Hello",))


def test_fastapi_validation_exception(test_client: TestClient):
    _expect_error(test_client.post("/post-400", json={"test2": 5}), 400, (
        "body.test1: Field required",
        "body.test2: Input should be a valid string",
    ))
    _expect_error(
        test_client.post("/post-400", json={"test1": "a", "test2": {"a": "b"}}), 400,
        ("body.test2: Input should be a valid string",))


def test_fastapi_auth_public(fastapi_client_auth: TestClient):
    # can get service info (set up by boilerplate BentoFastAPI class)
    r = fastapi_client_auth.get("/service-info")
    assert r.status_code == 200
    rd = r.json()
    assert rd["version"] == TEST_APP_VERSION

    # can get service-info again; should use cached version now
    r = fastapi_client_auth.get("/service-info")
    assert r.status_code == 200
    rd2 = r.json()
    assert rd == rd2

    # can get the FastAPI docs
    r = fastapi_client_auth.get("/docs")
    assert r.status_code == 200

    # can get the OpenAPI schema
    r = fastapi_client_auth.get("/openapi.json")
    assert r.status_code == 200

    # can post to the exempted post endpoint
    r = fastapi_client_auth.post("/post-exempted", json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == 200

    # can post to the public post endpoint
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
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=authz_code, payload={"result": [[authz_res]]})
    r = fastapi_client_auth.post(
        test_url, headers=(TEST_AUTHZ_HEADERS if inc_headers else {}), json=TEST_AUTHZ_VALID_POST_BODY)
    assert r.status_code == test_code


def test_fastapi_auth_invalid_body(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": [[True]]})
    r = fastapi_client_auth.post("/post-private", headers=TEST_AUTHZ_HEADERS, json={"test1": "a"})
    assert r.status_code == 400


def test_fastapi_auth_500(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": [[True]]})
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
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": [[True]]})
    r = fastapi_client_auth.post("/post-with-token-in-body", json={"token": "test", "payload": "hello world"})
    assert r.status_code == 200
    assert r.text == '{"payload":"hello world"}'


def test_fastapi_auth_post_with_token_evaluate_one(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": [[True]]})
    r = fastapi_client_auth.post("/post-with-token-evaluate-one", json={"token": "test"})
    assert r.status_code == 200
    assert r.text == '{"payload":true}'


def test_fastapi_auth_post_with_token_evaluate_to_dict(aioresponse: aioresponses, fastapi_client_auth: TestClient):
    aioresponse.post("https://bento-auth.local/policy/evaluate", status=200, payload={"result": [[True]]})
    r = fastapi_client_auth.post("/post-with-token-evaluate-to-dict", json={"token": "test"})
    assert r.status_code == 200
    assert r.text == '{"payload":[{"ingest:data":true}]}'


def test_fastapi_auth_put_not_included(fastapi_client_auth: TestClient):
    r = fastapi_client_auth.put("/put-test", json=TEST_AUTHZ_VALID_POST_BODY)  # no authz needed, not included
    assert r.status_code == 200


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
        frozenset({P_INGEST_DATA}),
        {"everything": True},
    ) is None


def test_fastapi_get_workflows(fastapi_client_auth: TestClient):
    r = fastapi_client_auth.get("/workflows")
    assert r.status_code == 200
    assert len(r.json()["ingestion"]) == 1  # 1 ingestion workflow

    r = fastapi_client_auth.get("/workflows/")  # trailing slash should be OK too
    assert r.status_code == 200
    assert len(r.json()["ingestion"]) == 1  # 1 ingestion workflow

    r = fastapi_client_auth.get("/workflows/test")
    assert r.status_code == 200  # workflow metadata
    r = fastapi_client_auth.get("/workflows/test.wdl")
    assert r.status_code == 200  # workflow WDL file

    # no workflow with the ID "test2"
    r = fastapi_client_auth.get("/workflows/test2")
    assert r.status_code == 404
    r = fastapi_client_auth.get("/workflows/test2.wdl")
    assert r.status_code == 404
