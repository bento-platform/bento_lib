from geojson_pydantic import Feature, Point
from pydantic import BaseModel, ConfigDict

__all__ = ["GeoLocationProperties", "GeoLocation"]


class GeoLocationProperties(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str
    city: str
    country: str
    ISO3166alpha3: str  # TODO
    precision: str


class GeoLocation(Feature):
    geometry: Point
    properties: GeoLocationProperties | None = None
