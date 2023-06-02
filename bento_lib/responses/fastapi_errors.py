import logging
import traceback

from fastapi import status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from typing import Callable

from .errors import http_error

__all__ = [
    "http_exception_handler_factory",
    "validation_exception_handler",
]


def http_exception_handler_factory(logger: logging.Logger) -> Callable[[Request, HTTPException], Response]:
    def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        code = exc.status_code

        if code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(f"Encountered error:\n{traceback.format_exception(type(exc), exc, exc.__traceback__)}")

        return JSONResponse(http_error(code, exc.detail), status_code=code)

    return http_exception_handler


def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    code = status.HTTP_400_BAD_REQUEST
    return JSONResponse(
        http_error(code, *((".".join(e["loc"]) + ": " + e["msg"]) if e.get("loc") else e["msg"] for e in exc.errors())),
        status_code=code)
