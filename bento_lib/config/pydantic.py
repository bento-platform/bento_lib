import json

from bento_lib.logging import LogLevelLiteral
from bento_lib.service_info.constants import SERVICE_ORGANIZATION_C3G
from bento_lib.service_info.types import GA4GHServiceOrganizationModel
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict
from typing import Any

__all__ = [
    "CorsOriginsParsingEnvSettingsSource",
    "BentoBaseConfig",
]


CORS_ORIGINS_DEFAULT: tuple[str, ...] = ()


class CorsOriginsParsingEnvSettingsSource(EnvSettingsSource):
    def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:
        if field_name == "cors_origins":
            return tuple(x.strip() for x in value.split(";")) if value is not None else CORS_ORIGINS_DEFAULT
        return json.loads(value) if value_is_complex else value


class BentoBaseConfig(BaseSettings):
    bento_debug: bool = False
    bento_container_local: bool = False
    bento_validate_ssl: bool = True
    bento_authz_enabled: bool = True
    bento_authz_service_url: str  # Bento authorization service base URL

    service_id: str
    service_name: str
    service_description: str = ""  # If description is blank, it should be stripped out in the response
    # service_url_base_path: str = "http://127.0.0.1:5000"  # Base path to construct URIs from
    service_contact_url: str = "mailto:info@c3g.ca"
    service_organization: GA4GHServiceOrganizationModel = SERVICE_ORGANIZATION_C3G

    log_level: LogLevelLiteral = "debug"

    cors_origins: tuple[str, ...] = CORS_ORIGINS_DEFAULT

    # Make Config instances hashable + immutable
    model_config = SettingsConfigDict(frozen=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CorsOriginsParsingEnvSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )
