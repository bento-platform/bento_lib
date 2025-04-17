import json

from flask import Flask, Request, Response, current_app, g, request
from functools import wraps

from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.base import BaseAuthMiddleware
from bento_lib.auth.permissions import Permission
from bento_lib.auth.resources import RESOURCE_EVERYTHING
from bento_lib.responses.errors import http_error

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

        if self._logger is None:
            self._logger = app.logger

    def middleware_pre(self) -> None:
        if self.enabled:
            g.bento_determined_authz = False

    def _make_auth_error(self, e: BentoAuthException) -> Response:
        # returning an error, so mark authz flow as 'done' (rejecting in one way or another):
        self.mark_authz_done(request)
        # return error response:
        return Response(
            json.dumps(
                http_error(
                    e.status_code,
                    e.message,
                    drs_compat=self._drs_compat,
                    sr_compat=self._sr_compat,
                    beacon_meta_callback=self._beacon_meta_callback,
                )
            ),
            status=e.status_code,
            content_type="application/json",
        )

    def _make_forbidden(self) -> Response:
        return self._make_auth_error(BentoAuthException("Forbidden", status_code=403))

    def middleware_post(self, response: Response) -> Response:
        if not self.enabled or self.request_is_exempt(request.method, request.path):
            # - Skip checks if the authorization middleware is disabled
            # - Allow pre-flight responses through, as well as any configured exempt URLs
            return response
        if not g.bento_determined_authz:
            return self._make_forbidden()
        return response

    @staticmethod
    def mark_authz_done(_request: Request):
        g.bento_determined_authz = True

    def get_authz_header_value(self, r: Request) -> str | None:
        return r.headers.get("Authorization")

    # TODO: IMPL SYNC + ASYNC + TEST
    # def get_permissions_on_resource(self, resource: dict):
    #     return self.authz_post(
    #         request,
    #         "/policy/list-permissions",
    #         {"requested_resource": resource},
    #         require_token=False,
    #     ).get("result")

    def deco_require_permissions_on_resource(
        self,
        permissions: frozenset[Permission],
        resource: dict | None = None,
        require_token: bool = True,
        set_authz_flag: bool = True,
    ):
        resource = resource or RESOURCE_EVERYTHING  # If no resource specified, require the permissions node-wide.

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if self.enabled:
                    try:
                        self.check_authz_evaluate(request, permissions, resource, require_token, set_authz_flag)
                    except BentoAuthException as e:
                        return self._make_auth_error(e)
                return current_app.ensure_sync(func)(*args, **kwargs)

            return wrapper

        return decorator

    def deco_public_endpoint(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            res = current_app.ensure_sync(func)(*args, **kwargs)
            if self.enabled:
                self.mark_authz_done(request)
            return res

        return wrapper
