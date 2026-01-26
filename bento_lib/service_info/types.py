from pydantic import BaseModel, ConfigDict
from typing import Literal, NotRequired, Required, TypedDict

__all__ = [
    "GA4GHServiceType",
    "GA4GHServiceOrganization",
    "GA4GHServiceOrganizationModel",
    "BentoExtraServiceInfo",
    "GA4GHServiceInfo",
    "BentoServiceRecord",
    "BentoDataTypeServiceListing",
    "BentoDataType",
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


class BentoExtraServiceInfo(TypedDict, total=False):
    serviceKind: Required[str]  # One service_kind per Bento service/instance
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


class GA4GHServiceInfo(TypedDict):
    id: str
    name: str
    type: GA4GHServiceType
    organization: GA4GHServiceOrganization
    version: str
    # -- Optional fields: --------------------------
    description: NotRequired[str]
    contactUrl: NotRequired[str]
    documentationUrl: NotRequired[str]
    url: NotRequired[str]  # Technically not part of spec; comes from service-registry
    environment: NotRequired[Literal["dev", "prod"]]
    # Bento-specific service info properties are contained inside a nested, "bento"-keyed dictionary
    bento: NotRequired[BentoExtraServiceInfo]


class BentoServiceRecord(TypedDict):
    service_kind: str
    url_template: str
    repository: str
    url: str


class BentoDataTypeServiceListing(TypedDict):
    queryable: bool
    item_schema: dict
    metadata_schema: dict
    id: str
    count: int | None
    label: NotRequired[str | None]


class BentoDataType(TypedDict):
    service_base_url: str
    data_type_listing: BentoDataTypeServiceListing
