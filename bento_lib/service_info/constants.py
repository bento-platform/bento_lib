from typing import Literal
from .types import GA4GHServiceOrganization, GA4GHServiceOrganizationModel

__all__ = [
    "SERVICE_ENVIRONMENT_DEV",
    "SERVICE_ENVIRONMENT_PROD",
    "SERVICE_ORGANIZATION_C3G",
    "SERVICE_ORGANIZATION_C3G_PYDANTIC",
    "SERVICE_GROUP_BENTO",
]


SERVICE_ENVIRONMENT_DEV: Literal["dev"] = "dev"
SERVICE_ENVIRONMENT_PROD: Literal["prod"] = "prod"

SERVICE_ORGANIZATION_C3G: GA4GHServiceOrganization = {"name": "C3G", "url": "https://www.computationalgenomics.ca"}
SERVICE_ORGANIZATION_C3G_PYDANTIC: GA4GHServiceOrganizationModel = GA4GHServiceOrganizationModel.model_validate(
    SERVICE_ORGANIZATION_C3G
)

SERVICE_GROUP_BENTO = "ca.c3g.bento"
