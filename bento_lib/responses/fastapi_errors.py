import traceback

from fastapi import status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from typing import Callable

from ..auth.exceptions import BentoAuthException
from ..auth.types import MarkAuthzDoneType
from ..logging.types import StdOrBoundLogger
from .errors import http_error

__all__ = [
    "http_exception_handler_factory",
    "bento_auth_exception_handler_factory",
    "validation_exception_handler_factory",
]


def _log_if_500(logger: StdOrBoundLogger, code: int, exc: Exception) -> None:
    if code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(f"Encountered error:\n{traceback.format_exception(type(exc), exc, exc.__traceback__)}")


def http_exception_handler_factory(
    logger: StdOrBoundLogger,
    authz: MarkAuthzDoneType | None = None,
    **kwargs,
) -> Callable[[Request, HTTPException], Response]:
    def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if authz:
            authz.mark_authz_done(request)
        code = exc.status_code
        _log_if_500(logger, code, exc)
        return JSONResponse(http_error(code, exc.detail, **kwargs), status_code=code)

    return http_exception_handler


def bento_auth_exception_handler_factory(
    logger: StdOrBoundLogger,
    authz: MarkAuthzDoneType | None = None,
    **kwargs,
) -> Callable[[Request, BentoAuthException], Response]:
    def bento_auth_exception_handler(request: Request, exc: BentoAuthException) -> JSONResponse:
        if authz:
            authz.mark_authz_done(request)
        code = exc.status_code
        _log_if_500(logger, code, exc)
        return JSONResponse(http_error(code, exc.message, **kwargs), status_code=code)

    return bento_auth_exception_handler


def validation_exception_handler_factory(
    authz: MarkAuthzDoneType | None = None,
    **kwargs,
) -> Callable[[Request, RequestValidationError], Response]:
    def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        if authz:
            authz.mark_authz_done(request)
        code = status.HTTP_400_BAD_REQUEST
        return JSONResponse(
            http_error(
                code,
                *((".".join(map(str, e["loc"])) + ": " + e["msg"]) if e.get("loc") else e["msg"] for e in exc.errors()),
                **kwargs,
            ),
            status_code=code,
        )

    return validation_exception_handler
