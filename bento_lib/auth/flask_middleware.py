import json
import jwt
import logging
import requests
import time

from flask import Flask, Response, request, g
from functools import wraps
from jwt.api_jwk import PyJWK, PyJWKSet
from threading import Thread
from typing import FrozenSet, Optional, Tuple
from werkzeug.exceptions import BadRequest

from .exceptions import BentoAuthException
from ..responses.errors import http_error


RESOURCE_EVERYTHING = {"everything": True}


class FlaskAuthMiddleware:
    def __init__(
        self,
        app: Flask,
        bento_authz_service_url: str,
        openid_config_url: str,
        openid_aud: str,
        disallowed_algorithms: FrozenSet[str] = frozenset({}),
        drs_compat: bool = False,
        sr_compat: bool = False,
        debug_mode: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self._app: Flask = app
        self._debug: bool = debug_mode

        self._drs_compat: bool = drs_compat
        self._sr_compat: bool = sr_compat

        self._bento_authz_service_url: str = bento_authz_service_url

        app.before_request(FlaskAuthMiddleware.middleware_pre)
        app.after_request(self.middleware_post)

        # Populated by key-rotation thread
        self._jwks: Tuple[PyJWK, ...] = ()
        self._openid_config: Optional[dict] = None

        self._openid_config_url: str = openid_config_url
        self._openid_aud: str = openid_aud

        self._disallowed_algorithms = disallowed_algorithms

        # initialize key-rotation-fetching background process
        fetch_jwks_background_thread = Thread(target=self.fetch_jwks)
        fetch_jwks_background_thread.daemon = True
        fetch_jwks_background_thread.start()

        self._logger = logger or logging.getLogger(__name__)

    @staticmethod
    def middleware_pre() -> None:
        g.bento_determined_authz = None

    def _make_forbidden(self) -> Response:
        self.mark_authz_done()
        return Response(
            json.dumps(http_error(401, "Forbidden", drs_compat=self._drs_compat, sr_compat=self._sr_compat)),
            status=401,
            content_type="application/json")

    def middleware_post(self, response: Response) -> Response:
        if not g.bento_determined_authz:
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
        resource = resource or RESOURCE_EVERYTHING  # If no resource specified, require the permissions node-wide.

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                tkn = request.headers.get("Authorization")

                if require_token:
                    if tkn is None:
                        return self._make_forbidden()
                    try:
                        self.verify_token(tkn.split(" ")[1])
                    except BentoAuthException as e:
                        self._logger.error(f"Encountered auth exception during request: {e}")
                        return self._make_forbidden()
                    except IndexError:
                        # Bad split, return 400
                        raise BadRequest("Malformatted authorization header")

                res = requests.post(
                    f"{self._bento_authz_service_url.rstrip('/')}/policy/evaluate",
                    json={"requested_resource": resource, "required_permissions": list(permissions)},
                    headers=({"Authorization": tkn} if tkn else {}))

                if res.status_code != 200:  # Evaluation failed f
                    self._logger.error(
                        f"Got non-200 response from authorization service: {res.status_code} {res.content}")
                    return self._make_forbidden()

                if not res.json().get("result"):
                    # We early-return with the flag set - we're returning Forbidden,
                    # and we've determined authz, so we can just set the flag.
                    return self._make_forbidden()

                if set_authz_flag:
                    self.mark_authz_done()

                return func(*args, **kwargs)
            return wrapper
        return decorator

    def fetch_jwks(self):
        while True:
            if not self._openid_config:
                r = requests.get(self._openid_config_url, verify=not self._debug)
                self._openid_config = r.json()

            # Manually do JWK signing key fetching. This way, we can turn off SSL verification in debug mode.

            r = requests.get(self._openid_config["jwks_uri"], verify=not self._debug)
            jwks = r.json()
            jwk_set = PyJWKSet.from_dict(jwks)

            self._jwks = tuple(k for k in jwk_set.keys if k.public_key_use in ("sig", None) and k.key_id)

            time.sleep(60)  # sleep 1 minute

    # def verify_token_optional(self):
    #     g.authn = {}
    #     if request.headers.get("Authorization"):
    #         self.verify_token()
    #
    # def verify_token_required(self):
    #     g.authn = {}
    #     if request.headers.get("Authorization"):
    #         self.verify_token()
    #     else:
    #         raise BentoAuthException('Missing access token')

    def verify_token(self, token: str):
        # Assume is Bearer token
        # authz_str_split = request.headers.get("Authorization").split(" ")
        #
        # if len(authz_str_split) <= 1:  # Bad token
        #     raise BentoAuthException("Malformed access_token")
        #
        # token_str = authz_str_split[1]

        # use idp public_key to validate and parse inbound token
        try:
            header = jwt.get_unverified_header(token)
            signing_key = next((k for k in self._jwks if k.key_id == header["kid"]), None)
            if signing_key is None:
                raise BentoAuthException("Could not find signing key")
            if (alg := header["alg"]) is None or alg in self._disallowed_algorithms:
                raise BentoAuthException("Disallowed signing algorithm")
            return jwt.decode(
                token, signing_key.key, algorithms=[signing_key.Algorithm], audience=self._openid_aud)
        # specific jwt errors
        except jwt.exceptions.ExpiredSignatureError:
            raise BentoAuthException('Expired access token')
        # less-specific jwt errors
        except jwt.exceptions.InvalidTokenError:
            raise BentoAuthException('Invalid access token')
        # general jwt errors
        except jwt.exceptions.PyJWTError:
            raise BentoAuthException('Access token error')
        # other
        except Exception:
            raise BentoAuthException('Access token error')

        # g.authn['has_valid_token'] = True
        #
        # # parse out relevant roles
        # if 'resource_access' in payload.keys() and \
        #         str(self.client_id) in payload["resource_access"].keys() and \
        #         'roles' in payload["resource_access"][self.client_id].keys():
        #     roles = payload["resource_access"][self.client_id]["roles"]
        #     print(roles)
        #
        #     g.authn['roles'] = roles
