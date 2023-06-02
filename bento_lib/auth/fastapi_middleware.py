from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Awaitable, Callable

from bento_lib.responses.errors import http_error
from .exceptions import BentoAuthException
from .middleware.base import BaseAuthMiddleware


class FastApiAuthMiddleware(BaseAuthMiddleware, BaseHTTPMiddleware):
    def attach(self, app: FastAPI):
        """
        Attach the middleware to an application. Must be called in order for requests to be checked.
        :param app: A FastAPI application.
        """
        app.middleware("http")(self)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method == "OPTIONS":  # Allow pre-flight responses through
            return await call_next(request)

        # Set flag saying the request hasn't had its permissions determined yet.
        request.state.bento_determined_authz = False

        try:
            res: Response = await call_next(request)
            if not request.state.bento_determined_authz:
                # Next in response chain didn't properly think about auth; return 403
                raise BentoAuthException(status_code=status.HTTP_403_FORBIDDEN, message="Forbidden")

        except BentoAuthException as e:
            request.state.bento_determined_authz = True
            return JSONResponse(
                status_code=e.status_code,
                content=http_error(e.status_code, e.message, drs_compat=self._drs_compat, sr_compat=self._sr_compat))

        # Otherwise, return the response as normal
        return res
