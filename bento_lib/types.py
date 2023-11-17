from pydantic import BaseModel, ConfigDict
from typing import TypedDict

__all__ = [
    "GA4GHServiceType",
    "GA4GHServiceOrganization",
    "GA4GhServiceOrganizationModel",
    "SERVICE_ORGANIZATION_C3G",
    "SERVICE_ORGANIZATION_C3G_PYDANTIC",
    "BentoExtraServiceInfo",
    "GA4GHServiceInfo",
]


class GA4GHServiceType(TypedDict):
    group: str
    artifact: str
    version: str


class GA4GHServiceOrganization(TypedDict):
    name: str
    url: str


class GA4GhServiceOrganizationModel(BaseModel):
    name: str
    url: str
    model_config = ConfigDict(extra="forbid")


SERVICE_ORGANIZATION_C3G: GA4GHServiceOrganization = {"name": "C3G", "url": "https://www.computationalgenomics.ca"}
SERVICE_ORGANIZATION_C3G_PYDANTIC: GA4GhServiceOrganizationModel = GA4GhServiceOrganizationModel.model_validate(
    SERVICE_ORGANIZATION_C3G)


# TODO: py3.11: Required[] instead of base class


class BentoExtraServiceInfo(TypedDict, total=False):
    serviceKind: str  # One service_kind per Bento service/instance
    dataService: bool  # Whether the service provides data types/search/workflows
    # Whether the service provides workflows:
    #   - not necessarily data types; split from dataService to allow services to provide workflows
    #     without needing to provide data types/search endpoints as well
    #   - implict default: false
    workflowProvider: bool
    # Git information: only added if we're in a local development mode
    gitRepository: str
    gitTag: str
    gitBranch: str
    gitCommit: str


class _GA4GHServiceInfoBase(TypedDict):
    id: str
    name: str
    type: GA4GHServiceType
    organization: GA4GHServiceOrganization
    version: str


class GA4GHServiceInfo(_GA4GHServiceInfoBase, total=False):
    description: str
    contactUrl: str
    documentationUrl: str
    url: str  # Technically not part of spec; comes from service-registry
    environment: str  # TODO: Literal["dev", "prod"] if JetBrains fixes their inspection...
    # Bento-specific service info properties are contained inside a nested, "bento"-keyed dictionary
    bento: BentoExtraServiceInfo
