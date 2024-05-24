import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse

from bento_lib.auth.exceptions import BentoAuthException
from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.config.pydantic import BentoFastAPIBaseConfig
from bento_lib.responses.fastapi_errors import (
    bento_auth_exception_handler_factory,
    http_exception_handler_factory,
    validation_exception_handler_factory,
)
from bento_lib.service_info.helpers import build_service_info_from_pydantic_config
from bento_lib.service_info.types import BentoExtraServiceInfo, GA4GHServiceInfo, GA4GHServiceType

__all__ = ["BentoFastAPI"]


class BentoFastAPI(FastAPI):
    def __init__(
        self,
        authz_middleware: FastApiAuthMiddleware | None,
        config: BentoFastAPIBaseConfig,
        logger: logging.Logger,
        bento_extra_service_info: BentoExtraServiceInfo,
        service_type: GA4GHServiceType,
        version: str,
        exc_handler_kwargs: dict | None = None,
        *args,
        **kwargs,
    ):
        app_kwargs = dict(
            title=config.service_name,
            root_path=urlparse(config.service_url_base_path).path,
            docs_url=config.service_docs_path,
            openapi_url=config.service_openapi_path,
            version=version,
            **kwargs,
        )

        super().__init__(*args, **app_kwargs)

        self._config = config
        self._logger = logger
        self._bento_extra_service_info = bento_extra_service_info
        self._service_type = service_type
        self._version = version

        # Set up CORS
        self.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_headers=["Authorization", "Cache-Control"],
            allow_methods=["*"],
        )

        # Set up authorization
        #  - Non-standard middleware setup so that we can import the instance and use it for dependencies too
        if authz_middleware:
            authz_middleware.attach(self)

        # Set up exception handlers for standard Bento/FastAPI errors
        exc_handler_kwargs = exc_handler_kwargs or {}
        self.exception_handler(BentoAuthException)(
            bento_auth_exception_handler_factory(logger, authz_middleware, **exc_handler_kwargs))
        self.exception_handler(StarletteHTTPException)(
            http_exception_handler_factory(logger, authz_middleware, **exc_handler_kwargs))
        self.exception_handler(RequestValidationError)(
            validation_exception_handler_factory(authz_middleware, **exc_handler_kwargs))

        # Set up service info endpoint

        self._service_info: GA4GHServiceInfo | None = None

        si_deps = [authz_middleware.dep_public_endpoint()] if authz_middleware else []

        @self.get("/service-info", dependencies=si_deps)
        async def service_info():
            return await self.get_service_info()

    async def get_service_info(self) -> GA4GHServiceInfo:
        if not self._service_info:
            self._service_info = await build_service_info_from_pydantic_config(
                self._config, self._logger, self._bento_extra_service_info, self._service_type, self._version)
        return self._service_info
