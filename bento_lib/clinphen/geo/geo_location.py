from pydantic import BaseModel, ConfigDict
from typing import Literal

__all__ = ["GeoLocationProperties", "GeoLocation"]


class GeoLocationProperties(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str
    city: str
    country: str
    ISO3166alpha3: str  # TODO
    precision: str


# TODO: inherit from GeoJSON model instead?
class GeoLocation(BaseModel):
    type: Literal["Feature"]
    geometry: TODO
    properties: GeoLocationProperties
