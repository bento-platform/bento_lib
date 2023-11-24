import logging

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from typing import Awaitable, Callable

from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.base import BaseAuthMiddleware
from bento_lib.auth.permissions import Permission
from bento_lib.auth.resources import RESOURCE_EVERYTHING
from bento_lib.responses.errors import http_error

__all__ = [
    "FastApiAuthMiddleware",
]


class FastApiAuthMiddleware(BaseAuthMiddleware):
    def attach(self, app: FastAPI):
        """
        Attach the middleware to an application. Must be called in order for requests to be checked.
        :param app: A FastAPI application.
        """

        # Attach our instance's dispatch method to the FastAPI instance as a middleware function
        app.middleware("http")(self.dispatch)

        # If no logger was passed, create a new logger
        if self._logger is None:
            self._logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not self.enabled or request.method == "OPTIONS":
            # - Skip checks if the authorization middleware is disabled
            # - Allow pre-flight responses through
            return await call_next(request)

        # Set flag saying the request hasn't had its permissions determined yet.
        request.state.bento_determined_authz = False

        try:
            res: Response = await call_next(request)
            if not request.state.bento_determined_authz:
                # Next in response chain didn't properly think about auth; return 403
                raise BentoAuthException(status_code=status.HTTP_403_FORBIDDEN, message="Forbidden")

        except BentoAuthException as e:
            self.mark_authz_done(request)
            return JSONResponse(
                status_code=e.status_code,
                content=http_error(
                    e.status_code,
                    e.message,
                    drs_compat=self._drs_compat,
                    sr_compat=self._sr_compat,
                    beacon_meta_callback=self._beacon_meta_callback,
                ))

        # Otherwise, return the response as normal
        return res

    def get_authz_header_value(self, request: Request) -> str | None:
        return request.headers.get("Authorization")

    @staticmethod
    def mark_authz_done(request: Request):
        request.state.bento_determined_authz = True

    def dep_public_endpoint(self):
        def _inner(request: Request):
            if not self.enabled:
                return
            self.mark_authz_done(request)
        return Depends(_inner)

    def dep_require_permissions_on_resource(
        self,
        permissions: frozenset[Permission],
        resource: dict | None = None,
        require_token: bool = True,
        set_authz_flag: bool = True,
    ):
        resource = resource or RESOURCE_EVERYTHING

        async def _inner(request: Request):
            if not self.enabled:
                return

            await self.async_check_authz_evaluate(
                request,
                permissions,
                resource,
                require_token=require_token,
                set_authz_flag=set_authz_flag,
            )

        return Depends(_inner)
