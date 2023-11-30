from pydantic import BaseModel, ConfigDict
from typing import Literal, TypedDict

__all__ = [
    "GA4GHServiceType",
    "GA4GHServiceOrganization",
    "GA4GHServiceOrganizationModel",
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


class GA4GHServiceOrganizationModel(BaseModel):
    name: str
    url: str
    # frozen=True makes this hashable + immutable
    model_config = ConfigDict(extra="forbid", frozen=True)


# TODO: py3.11: Required[] instead of base class


class BentoExtraServiceInfo(TypedDict, total=False):
    serviceKind: str  # One service_kind per Bento service/instance
    dataService: bool  # Whether the service provides data types/search/workflows
    # Whether the service provides workflows:
    #   - not necessarily data types; split from dataService to allow services to provide workflows
    #     without needing to provide data types/search endpoints as well
    #   - implict default: false
    workflowProvider: bool
    # Git:
    #  - Static Git information: should be set by service developers
    gitRepository: str
    #  - Dynamic Git information: only added if we're in a local development mode
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
    environment: Literal["dev", "prod"]
    # Bento-specific service info properties are contained inside a nested, "bento"-keyed dictionary
    bento: BentoExtraServiceInfo
