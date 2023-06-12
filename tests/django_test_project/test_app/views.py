import json
from bento_lib.auth.middleware.constants import RESOURCE_EVERYTHING
from django.http import HttpRequest, JsonResponse

from ..django_test_project.authz import authz

PERMISSION_INGEST_DATA = "ingest:data"


def auth_post_public(request: HttpRequest):
    authz.mark_authz_done(request)
    return JsonResponse(json.loads(request.body))


def auth_post_private(request: HttpRequest):
    authz.check_authz_evaluate(
        request,
        frozenset({PERMISSION_INGEST_DATA}),
        RESOURCE_EVERYTHING,
        require_token=True,
        set_authz_flag=True,
    )
    return JsonResponse(json.loads(request.body))


def auth_post_private_no_flag(request: HttpRequest):
    authz.check_authz_evaluate(
        request,
        frozenset({PERMISSION_INGEST_DATA}),
        RESOURCE_EVERYTHING,
        require_token=True,
        set_authz_flag=False,
    )
    authz.mark_authz_done(request)
    return JsonResponse(json.loads(request.body))


def auth_post_private_no_token(request: HttpRequest):
    authz.check_authz_evaluate(
        request,
        frozenset({PERMISSION_INGEST_DATA}),
        RESOURCE_EVERYTHING,
        require_token=False,
        set_authz_flag=True,
    )
    return JsonResponse(json.loads(request.body))


def auth_post_missing_authz(request: HttpRequest):
    return JsonResponse(json.loads(request.body))  # no authz flag set, so will return a 403


def auth_post_exception(_request: HttpRequest):
    raise Exception("hello")
