import aiohttp
import jwt
import logging
import requests
import time

from abc import ABC, abstractmethod
from jwt import PyJWK, PyJWKSet
from threading import Thread
from typing import Any

from ..exceptions import BentoAuthException

__all__ = ["BaseAuthMiddleware"]


class BaseAuthMiddleware(ABC):
    def __init__(
        self,
        bento_authz_service_url: str,
        openid_config_url: str,
        openid_aud: str = "account",
        disallowed_algorithms: frozenset[str] = frozenset({}),
        drs_compat: bool = False,
        sr_compat: bool = False,
        debug_mode: bool = False,
        enabled: bool = True,
        logger: logging.Logger | None = None,
    ):
        self._debug: bool = debug_mode
        self._verify_ssl: bool = not debug_mode

        self._enabled: bool = enabled
        self._logger = logger or logging.getLogger(__name__)

        self._drs_compat: bool = drs_compat
        self._sr_compat: bool = sr_compat

        self._bento_authz_service_url: str = bento_authz_service_url

        # Populated by key-rotation thread vvv
        self._jwks: tuple[PyJWK, ...] = ()
        self._openid_config: dict | None = None
        # ^^^

        self._openid_config_url: str = openid_config_url
        self._openid_aud: str = openid_aud

        self._disallowed_algorithms = disallowed_algorithms

        if self.enabled:
            # initialize key-rotation-fetching background process:
            self._fetch_jwks_background_thread = Thread(target=self._fetch_jwks)
            self._fetch_jwks_background_thread.daemon = True
            self._fetch_jwks_background_thread.start()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _fetch_jwks(self):
        while self.enabled:
            if not self._openid_config:
                r = requests.get(self._openid_config_url, verify=self._verify_ssl)
                self._openid_config = r.json()

            # Manually do JWK signing key fetching. This way, we can turn off SSL verification in debug mode.

            r = requests.get(self._openid_config["jwks_uri"], verify=self._verify_ssl)
            jwks = r.json()
            jwk_set = PyJWKSet.from_dict(jwks)

            self._jwks = tuple(k for k in jwk_set.keys if k.public_key_use in ("sig", None) and k.key_id)

            time.sleep(60)  # sleep 1 minute

    def verify_token(self, token: str):
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
            raise BentoAuthException("Expired access token")
        # less-specific jwt errors
        except jwt.exceptions.InvalidTokenError:
            raise BentoAuthException("Invalid access token")
        # general jwt errors
        except jwt.exceptions.PyJWTError:
            raise BentoAuthException("Access token error")
        # other
        except Exception:
            raise BentoAuthException("Access token error")

    @abstractmethod
    def get_authz_header_value(self, request: Any) -> str | None:  # pragma: no cover
        pass

    @staticmethod
    def check_require_token(require_token: bool, token: str | None) -> None:
        if require_token:
            if token is None:
                raise BentoAuthException("No token provided")

    def verify_token_from_header_and_raise(self, token_header: str | None) -> None:
        if token_header is not None:
            try:
                self.verify_token(token_header.split(" ")[1])
            except BentoAuthException as e:
                self._logger.error(f"Encountered auth exception during request: {e}")
                raise e  # Re-raise - pass it up
            except IndexError:
                # Bad split, return 400
                raise BentoAuthException("Malformatted authorization header", status_code=400)

    def mk_authz_url(self, path: str) -> str:
        return f"{self._bento_authz_service_url.rstrip('/')}{path}"

    def authz_post(self, request: Any, path: str, body: dict, require_token: bool = False) -> dict:
        tkn_header = self.get_authz_header_value(request)

        self.check_require_token(require_token, tkn_header)
        self.verify_token_from_header_and_raise(tkn_header)

        res = requests.post(
            self.mk_authz_url(path),
            json=body,
            headers=({"Authorization": tkn_header} if tkn_header else {}), verify=self._verify_ssl)

        if res.status_code != 200:  # Evaluation failed f
            self._logger.error(
                f"Got non-200 response from authorization service: {res.status_code} {res.content}")
            # Generic error - don't leak errors from authz service!
            raise BentoAuthException("Error from authz service", status_code=500)

        return res.json()

    async def async_authz_post(self, request: Any, path: str, body: dict, require_token: bool = False) -> dict:
        tkn_header = self.get_authz_header_value(request)

        self.check_require_token(require_token, tkn_header)
        self.verify_token_from_header_and_raise(tkn_header)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.mk_authz_url(path),
                    json=body,
                    headers=({"Authorization": tkn_header} if tkn_header else {}),
                    ssl=(None if self._verify_ssl else False)) as res:
                if res.status != 200:  # Evaluation failed f
                    self._logger.error(
                        f"Got non-200 response from authorization service: {res.status} {await res.text()}")
                    # Generic error - don't leak errors from authz service!
                    raise BentoAuthException("Error from authz service", status_code=500)
                return await res.json()

    @staticmethod
    @abstractmethod
    def mark_authz_done(request: Any):  # pragma: no cover
        pass

    async def async_check_authz_evaluate(
        self,
        request: Any,
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
            self.mark_authz_done(request)
