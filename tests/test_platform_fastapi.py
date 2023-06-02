import logging
import pytest

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

from bento_lib.responses.fastapi_errors import (
    http_exception_handler_factory,
    validation_exception_handler,
)


logger = logging.getLogger(__name__)

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


def test_fastapi_http_exception_404(test_client: TestClient):
    r = test_client.get("/get-404")
    assert r.status_code == 404
    data = r.json()
    assert data["code"] == 404
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Hello"


def test_fastapi_http_exception_500(test_client: TestClient):
    r = test_client.get("/get-500")
    assert r.status_code == 500
    data = r.json()
    assert data["code"] == 500
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Hello"


def test_fastapi_validation_exception(test_client: TestClient):
    r = test_client.post("/post-400", json={"test2": 5})
    assert r.status_code == 400
    data = r.json()
    assert data["code"] == 400
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "body.test1: field required"

    r = test_client.post("/post-400", json={"test1": "a", "test2": {"a": "b"}})
    assert r.status_code == 400
    data = r.json()
    assert data["code"] == 400
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "body.test2: str type expected"
