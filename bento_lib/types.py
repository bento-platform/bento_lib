from typing import TypedDict

__all__ = [
    "GA4GHServiceType",
    "GA4GHServiceOrganization",
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

    # TODO: put these in their own Bento object?
    git_tag: str
    git_branch: str
