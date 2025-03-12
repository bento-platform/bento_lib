import aiohttp
import re
import requests

from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable

from bento_lib.config.pydantic import BentoBaseConfig
from bento_lib.logging.types import StdOrBoundLogger
from ..exceptions import BentoAuthException
from ..permissions import Permission
from ..types import EvaluationResultMatrix, EvaluationResultDict
from .mark_authz_done_mixin import MarkAuthzDoneMixin

__all__ = ["BaseAuthMiddleware"]


NonNormalizedPattern = re.Pattern | str

# Order: method pattern, path pattern
NonNormalizedRequestPattern = tuple[NonNormalizedPattern, NonNormalizedPattern]
NonNormalizedRequestPatterns = tuple[NonNormalizedRequestPattern, ...]
RequestPattern = tuple[re.Pattern, re.Pattern]
RequestPatterns = frozenset[RequestPattern]


def _compile_to_regex_if_needed(pattern: NonNormalizedPattern) -> re.Pattern:
    if isinstance(pattern, str):
        return re.compile(pattern)
    return pattern


def _normalize_request_patterns(patterns: NonNormalizedRequestPatterns) -> RequestPatterns:
    return frozenset(
        (_compile_to_regex_if_needed(method_pattern), _compile_to_regex_if_needed(path_pattern))
        for method_pattern, path_pattern in patterns
    )


def _request_pattern_match(method: str, path: str, patterns: RequestPatterns) -> tuple[bool, ...]:
    return tuple(bool(mp.fullmatch(method) and pp.fullmatch(path)) for mp, pp in patterns)


class BaseAuthMiddleware(ABC, MarkAuthzDoneMixin):
    def __init__(
        self,
        bento_authz_service_url: str,
        drs_compat: bool = False,
        sr_compat: bool = False,
        beacon_meta_callback: Callable[[], dict] | None = None,
        include_request_patterns: NonNormalizedRequestPatterns | None = None,
        exempt_request_patterns: NonNormalizedRequestPatterns = (),
        debug_mode: bool = False,
        enabled: bool = True,
        logger: StdOrBoundLogger | None = None,
    ):
        self._debug: bool = debug_mode
        self._verify_ssl: bool = not debug_mode

        self._enabled: bool = enabled
        self._logger: StdOrBoundLogger | None = logger

        self._drs_compat: bool = drs_compat
        self._sr_compat: bool = sr_compat
        self._beacon_meta_callback: Callable[[], dict] | None = beacon_meta_callback

        self._include_request_patterns: RequestPatterns | None = (
            _normalize_request_patterns(include_request_patterns) if include_request_patterns is not None else None
        )
        self._exempt_request_patterns: RequestPatterns = _normalize_request_patterns(exempt_request_patterns)

        self._bento_authz_service_url: str = bento_authz_service_url

    @classmethod
    def build_from_pydantic_config(cls, config: BentoBaseConfig, logger: StdOrBoundLogger, **kwargs):
        return cls(
            bento_authz_service_url=config.bento_authz_service_url,
            debug_mode=config.bento_debug,
            enabled=config.bento_authz_enabled,
            logger=logger,
            **kwargs,
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def request_is_exempt(self, method: str, path: str) -> bool:
        return (
            method == "OPTIONS"
            or (
                self._include_request_patterns is not None
                and not any(_request_pattern_match(method, path, self._include_request_patterns))
            )
            or any(_request_pattern_match(method, path, self._exempt_request_patterns))
        )

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

    def _extract_token_and_build_headers(
        self,
        request: Any,
        require_token: bool,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
    ) -> dict[str, str]:
        if headers_getter:
            return headers_getter(request)

        tkn_header = self.get_authz_header_value(request)
        self.check_require_token(require_token, tkn_header)
        return {"Authorization": tkn_header} if tkn_header else {}

    def _log_error(self, message: str):
        if self._logger:
            self._logger.error(message)

    def _gen_exc_non_200_error_from_authz(self, code: int, content: bytes):
        self._log_error(f"Got non-200 response from authorization service: {code} {content!r}")
        # Generic error - don't leak errors from authz service!
        raise BentoAuthException("Error from authz service", status_code=500)

    def authz_post(
        self,
        request: Any,
        path: str,
        body: dict,
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
    ) -> dict:
        res = requests.post(
            self.mk_authz_url(path),
            json=body,
            headers=self._extract_token_and_build_headers(request, require_token, headers_getter),
            verify=self._verify_ssl,
        )

        if res.status_code != 200:  # Invalid authorization service response
            raise self._gen_exc_non_200_error_from_authz(res.status_code, res.content)

        return res.json()

    @staticmethod
    def _evaluate_body(resources: Iterable[dict], permissions: Iterable[Permission]) -> dict:
        return {"resources": tuple(resources), "permissions": tuple(permissions)}

    @staticmethod
    def _matrix_tuple_cast(authz_result: list[list[bool]]) -> EvaluationResultMatrix:
        return tuple(map(tuple, authz_result))

    @staticmethod
    def _permissions_matrix_to_dict(
        m: EvaluationResultMatrix,
        permissions: Iterable[Permission],
    ) -> EvaluationResultDict:
        return tuple(dict(zip(permissions, r)) for r in m)

    def evaluate(
        self,
        request: Any,
        resources: Iterable[dict],
        permissions: Iterable[Permission],
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
        mark_authz_done: bool = False,
    ) -> EvaluationResultMatrix:
        if mark_authz_done:
            self.mark_authz_done(request)
        return self._matrix_tuple_cast(
            self.authz_post(
                request,
                "/policy/evaluate",
                self._evaluate_body(resources, permissions),
                require_token=require_token,
                headers_getter=headers_getter,
            )["result"]
        )

    def evaluate_to_dict(
        self,
        request: Any,
        resources: Iterable[dict],
        permissions: Iterable[Permission],
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
        mark_authz_done: bool = False,
    ) -> EvaluationResultDict:
        # consume iterable only once in case it's a generator
        _perms = tuple(permissions)
        return self._permissions_matrix_to_dict(
            self.evaluate(request, resources, _perms, require_token, headers_getter, mark_authz_done), _perms
        )

    def evaluate_one(
        self,
        request: Any,
        resource: dict,
        permission: Permission,
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
        mark_authz_done: bool = False,
    ) -> bool:
        return self.evaluate(request, (resource,), (permission,), require_token, headers_getter, mark_authz_done)[0][0]

    async def async_authz_post(
        self,
        request: Any,
        path: str,
        body: dict,
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.mk_authz_url(path),
                json=body,
                headers=self._extract_token_and_build_headers(request, require_token, headers_getter),
                ssl=(None if self._verify_ssl else False),
            ) as res:
                if res.status != 200:  # Invalid authorization service response
                    raise self._gen_exc_non_200_error_from_authz(res.status, await res.content.read())

                return await res.json()

    async def async_evaluate(
        self,
        request: Any,
        resources: Iterable[dict],
        permissions: Iterable[Permission],
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
        mark_authz_done: bool = False,
    ) -> EvaluationResultMatrix:
        if mark_authz_done:
            self.mark_authz_done(request)
        return self._matrix_tuple_cast(
            (
                await self.async_authz_post(
                    request,
                    "/policy/evaluate",
                    self._evaluate_body(resources, permissions),
                    require_token=require_token,
                    headers_getter=headers_getter,
                )
            )["result"]
        )

    async def async_evaluate_to_dict(
        self,
        request: Any,
        resources: Iterable[dict],
        permissions: Iterable[Permission],
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
        mark_authz_done: bool = False,
    ) -> EvaluationResultDict:
        # consume iterable only once in case it's a generator
        _perms = tuple(permissions)
        return self._permissions_matrix_to_dict(
            await self.async_evaluate(request, resources, _perms, require_token, headers_getter, mark_authz_done),
            _perms,
        )

    async def async_evaluate_one(
        self,
        request: Any,
        resource: dict,
        permission: Permission,
        require_token: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
        mark_authz_done: bool = False,
    ) -> bool:
        return (
            await self.async_evaluate(
                request, (resource,), (permission,), require_token, headers_getter, mark_authz_done
            )
        )[0][0]

    def check_authz_evaluate(
        self,
        request: Any,
        permissions: frozenset[Permission],
        resource: dict,
        require_token: bool = True,
        set_authz_flag: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
    ) -> None:
        if not self.enabled:
            return

        res = self.evaluate(
            request,
            [resource],
            list(permissions),
            require_token=require_token,
            headers_getter=headers_getter,
            mark_authz_done=set_authz_flag,
        )[0]

        if not all(res):
            # We early-return with the flag set - we're returning Forbidden,
            # and we've determined authz, so we can just set the flag.
            raise BentoAuthException("Forbidden", status_code=403)  # Actually forbidden by authz service

    async def async_check_authz_evaluate(
        self,
        request: Any,
        permissions: frozenset[Permission],
        resource: dict,
        require_token: bool = True,
        set_authz_flag: bool = False,
        headers_getter: Callable[[Any], dict[str, str]] | None = None,
    ) -> None:
        if not self.enabled:
            return

        res = (
            await self.async_evaluate(
                request,
                [resource],
                list(permissions),
                require_token=require_token,
                headers_getter=headers_getter,
                mark_authz_done=set_authz_flag,
            )
        )[0]

        if not all(res):
            # We early-return with the flag set - we're returning Forbidden,
            # and we've determined authz, so we can just set the flag.
            raise BentoAuthException("Forbidden", status_code=403)  # Actually forbidden by authz service
