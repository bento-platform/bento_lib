from typing import Literal, TypedDict, Union

__all__ = [
    "GA4GHServiceType",
]


class GA4GHServiceType(TypedDict):
    group: str
    artifact: str
    version: str


class GA4GHServiceOrganization(TypedDict):
    name: str
    url: str


class GA4GHServiceInfo(TypedDict):
    id: str
    name: str
    type: GA4GHServiceType
    description: str
    organization: GA4GHServiceOrganization
    contactUrl: str
    version: str
    url: str
    environment: Union[Literal["dev"], Literal["prod"]]
