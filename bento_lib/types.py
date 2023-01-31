from typing import TypedDict

__all__ = [
    "GA4GHServiceType",
    "GA4GHServiceOrganization",
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


# TODO: py3.11: Required[] instead of base class


class BentoExtraServiceInfo(TypedDict, total=False):
    serviceKind: str  # One service_kind per Bento service/instance
    dataService: bool  # Whether the service provides data types/ingest workflows

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

    # TODO: deprecate in favour of bento object
    git_tag: str
    git_branch: str

    bento: BentoExtraServiceInfo
