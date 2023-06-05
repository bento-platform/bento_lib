from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from typing import Awaitable, Callable

from bento_lib.responses.errors import http_error
from .exceptions import BentoAuthException
from .middleware.base import BaseAuthMiddleware
from .middleware.constants import RESOURCE_EVERYTHING

__all__ = [
    "FastApiAuthMiddleware",
]


class FastApiAuthMiddleware(BaseAuthMiddleware):
    def attach(self, app: FastAPI):
        """
        Attach the middleware to an application. Must be called in order for requests to be checked.
        :param app: A FastAPI application.
        """
        app.middleware("http")(self.dispatch)

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

    def get_authz_header_value(self, request: Request) -> str | None:
        return request.headers.get("Authorization")

    async def require_permissions_on_resource(
        self,
        request: Request,
        permissions: frozenset[str],
        resource: dict,
        require_token: bool = True,
        set_authz_flag: bool = False,
    ):
        if not self.enabled:
            return

        res = await self.async_authz_post(
            request,
            "/policy/evaluate",
            body={"requested_resource": resource, "required_permissions": list(permissions)},
            require_token=require_token,
        )

        if not res.get("result"):
            # We early-return with the flag set - we're returning Forbidden,
            # and we've determined authz, so we can just set the flag.
            raise BentoAuthException("Forbidden", status_code=403)  # Actually forbidden by authz service

        if set_authz_flag:
            # Flag that we have thought about auth
            request.state.determined_authz = True

    def dep_require_permissions_on_resource(
        self,
        permissions: frozenset[str],
        resource: dict | None = None,
        require_token: bool = True,
    ):
        resource = resource or RESOURCE_EVERYTHING

        async def _inner(request: Request):
            await self.require_permissions_on_resource(
                request,
                permissions,
                resource,
                require_token=require_token,
                set_authz_flag=True,
            )

        return Depends(_inner)
