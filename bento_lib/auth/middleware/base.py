import aiohttp
import logging
import requests

from abc import ABC, abstractmethod
from typing import Any

from ..exceptions import BentoAuthException

__all__ = ["BaseAuthMiddleware"]


class BaseAuthMiddleware(ABC):
    def __init__(
        self,
        bento_authz_service_url: str,
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

    @property
    def enabled(self) -> bool:
        return self._enabled

    @abstractmethod
    def get_authz_header_value(self, request: Any) -> str | None:  # pragma: no cover
        pass

    @staticmethod
    def check_require_token(require_token: bool, token: str | None) -> None:
        if require_token:
            if token is None:
                raise BentoAuthException("No token provided")

    def mk_authz_url(self, path: str) -> str:
        return f"{self._bento_authz_service_url.rstrip('/')}{path}"

    def _extract_token_and_build_headers(self, request: Any, require_token: bool) -> dict:
        tkn_header = self.get_authz_header_value(request)
        self.check_require_token(require_token, tkn_header)
        return {"Authorization": tkn_header} if tkn_header else {}

    def _gen_exc_non_200_error_from_authz(self, code: int, content: bytes):
        self._logger.error(f"Got non-200 response from authorization service: {code} {content}")
        # Generic error - don't leak errors from authz service!
        raise BentoAuthException("Error from authz service", status_code=500)

    def authz_post(self, request: Any, path: str, body: dict, require_token: bool = False) -> dict:
        res = requests.post(
            self.mk_authz_url(path),
            json=body,
            headers=self._extract_token_and_build_headers(request, require_token),
            verify=self._verify_ssl)

        if res.status_code != 200:  # Invalid authorization service response
            raise self._gen_exc_non_200_error_from_authz(res.status_code, res.content)

        return res.json()

    async def async_authz_post(self, request: Any, path: str, body: dict, require_token: bool = False) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.mk_authz_url(path),
                    json=body,
                    headers=self._extract_token_and_build_headers(request, require_token),
                    ssl=(None if self._verify_ssl else False)) as res:

                if res.status != 200:  # Invalid authorization service response
                    raise self._gen_exc_non_200_error_from_authz(res.status, await res.content.read())

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
