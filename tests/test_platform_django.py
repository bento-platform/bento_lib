import pytest
import responses
from django.http import JsonResponse
from django.test import Client
from tests.django_test_project.django_test_project.authz import authz

from .common import (
    authz_test_case_params,
    authz_test_cases,
    TEST_AUTHZ_VALID_POST_BODY,
    TEST_AUTHZ_HEADERS,
)


def test_django_authz_logger_init():
    from bento_lib.auth.middleware.django import DjangoAuthMiddleware
    mw = DjangoAuthMiddleware("https://bento-auth.local")
    assert mw._logger is not None


@pytest.mark.parametrize(authz_test_case_params, authz_test_cases)
@responses.activate
def test_django_auth(
    # case variables
    authz_code: int,
    authz_res: bool,
    test_url: str,
    inc_headers: bool,
    test_code: int,
    # fixtures
    client: Client,
):
    responses.add(
        responses.POST,
        "https://bento-auth.local/policy/evaluate",
        json={"result": [[authz_res]]},
        status=authz_code,
    )
    r: JsonResponse = client.post(
        test_url,
        headers=(TEST_AUTHZ_HEADERS if inc_headers else {}),
        data=TEST_AUTHZ_VALID_POST_BODY,
        content_type="application/json")
    assert r.status_code == test_code


def test_django_exc(client: Client):
    with pytest.raises(Exception):
        client.post(
            "/post-exc",
            data=TEST_AUTHZ_VALID_POST_BODY,
            content_type="application/json")


def test_disabled(client: Client):
    authz._enabled = False
    r = client.post("/post-private", data=TEST_AUTHZ_VALID_POST_BODY, content_type="application/json")
    assert r.status_code == 200
