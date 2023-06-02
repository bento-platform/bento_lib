import json
import requests

from flask import Flask, Response, request, g
from functools import wraps
from typing import FrozenSet, Optional

from .exceptions import BentoAuthException
from .middleware.base import BaseAuthMiddleware
from ..responses.errors import http_error


RESOURCE_EVERYTHING = {"everything": True}


class FlaskAuthMiddleware(BaseAuthMiddleware):
    def attach(self, app: Flask):
        """
        Attach the middleware to an application. Must be called in order for requests to be checked.
        :param app: A Flask application.
        """
        app.before_request(FlaskAuthMiddleware.middleware_pre)
        app.after_request(self.middleware_post)

    @staticmethod
    def middleware_pre() -> None:
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
    def mark_authz_done():
        g.bento_determined_authz = True

    def require_resource_permissions(
        self,
        permissions: FrozenSet[str],
        resource: Optional[dict] = None,
        require_token: bool = True,
        set_authz_flag: bool = False,
    ):
        if not self.enabled:
            return

        resource = resource or RESOURCE_EVERYTHING  # If no resource specified, require the permissions node-wide.

        tkn = request.headers.get("Authorization")

        if require_token:
            if tkn is None:
                raise BentoAuthException("No token provided")
            try:
                self.verify_token(tkn.split(" ")[1])
            except BentoAuthException as e:
                self._logger.error(f"Encountered auth exception during request: {e}")
                raise e  # Re-raise - pass it up
            except IndexError:
                # Bad split, return 400
                raise BentoAuthException("Malformatted authorization header", status_code=400)

        res = requests.post(
            f"{self._bento_authz_service_url.rstrip('/')}/policy/evaluate",
            json={"requested_resource": resource, "required_permissions": list(permissions)},
            headers=({"Authorization": tkn} if tkn else {}))

        if res.status_code != 200:  # Evaluation failed f
            self._logger.error(
                f"Got non-200 response from authorization service: {res.status_code} {res.content}")
            # Generic error - don't leak errors from authz service!
            raise BentoAuthException("Error from authz service", status_code=500)

        if not res.json().get("result"):
            # We early-return with the flag set - we're returning Forbidden,
            # and we've determined authz, so we can just set the flag.
            raise BentoAuthException("Forbidden", status_code=403)  # Actually forbidden by authz service

        if set_authz_flag:
            self.mark_authz_done()

    def deco_require_resource_permissions(
        self,
        permissions: FrozenSet[str],
        resource: Optional[dict] = None,
        require_token: bool = True,
        set_authz_flag: bool = False,
    ):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    self.require_resource_permissions(permissions, resource, require_token, set_authz_flag)
                except BentoAuthException as e:
                    # returning an error, so mark authz flow as 'done' (rejecting in one way or another):
                    self.mark_authz_done()
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
