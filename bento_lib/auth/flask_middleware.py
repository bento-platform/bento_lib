import json

from flask import Flask, Request, Response, request, g
from functools import wraps

from .exceptions import BentoAuthException
from .middleware.base import BaseAuthMiddleware
from .middleware.constants import RESOURCE_EVERYTHING
from ..responses.errors import http_error

__all__ = [
    "FlaskAuthMiddleware",
]


class FlaskAuthMiddleware(BaseAuthMiddleware):
    def attach(self, app: Flask):
        """
        Attach the middleware to an application. Must be called in order for requests to be checked.
        :param app: A Flask application.
        """
        app.before_request(self.middleware_pre)
        app.after_request(self.middleware_post)

    def middleware_pre(self) -> None:
        if self.enabled:
            g.bento_determined_authz = False

    def _make_forbidden(self) -> Response:
        self.mark_authz_done()
        return Response(
            json.dumps(http_error(403, "Forbidden", drs_compat=self._drs_compat, sr_compat=self._sr_compat)),
            status=403,
            content_type="application/json")

    def middleware_post(self, response: Response) -> Response:
        if request.method == "OPTIONS":  # Allow pre-flight responses through
            return response
        if self.enabled and not g.bento_determined_authz:
            return self._make_forbidden()
        return response

    @staticmethod
    def mark_authz_done(_request: Request):
        g.bento_determined_authz = True

    def get_authz_header_value(self, r: Request) -> str | None:
        return r.headers.get("Authorization")

    def get_permissions_on_resource(self, resource: dict):
        return self.authz_post(
            request,
            "/policy/list-permissions",
            {"requested_resource": resource},
            require_token=False,
        ).get("result")

    def require_permissions_on_resource(
        self,
        permissions: frozenset[str],
        resource: dict | None = None,
        require_token: bool = True,
        set_authz_flag: bool = False,
    ):
        if not self.enabled:
            return

        resource = resource or RESOURCE_EVERYTHING  # If no resource specified, require the permissions node-wide.

        res = self.authz_post(
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
            self.mark_authz_done(request)

    def deco_require_permissions_on_resource(
        self,
        permissions: frozenset[str],
        resource: dict | None = None,
        require_token: bool = True,
        set_authz_flag: bool = False,
    ):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if self.enabled:
                    try:
                        self.require_permissions_on_resource(permissions, resource, require_token, set_authz_flag)
                    except BentoAuthException as e:
                        # returning an error, so mark authz flow as 'done' (rejecting in one way or another):
                        self.mark_authz_done(request)
                        # return error response:
                        return Response(
                            json.dumps(http_error(
                                e.status_code, e.message, drs_compat=self._drs_compat, sr_compat=self._sr_compat)),
                            status=e.status_code,
                            content_type="application/json",
                        )
                return func(*args, **kwargs)
            return wrapper
        return decorator
