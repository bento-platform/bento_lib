from geojson_pydantic import Polygon, Feature, FeatureCollection
from pydantic import BaseModel, Field, RootModel
from typing import Any, Literal
from ._internal import NoAdditionalProperties

__all__ = [
    "BarChart",
    "HistogramChart",
    "PieChart",
    "ChoroplethColorModeContinuous",
    "ChoroplethChart",
    "OverviewChart",
    "OverviewSection",
]


class BaseOverviewChart(BaseModel, NoAdditionalProperties):
    field: str = Field(
        ...,
        title="Field",
        description=(
            "Field ID, as defined by a key in the fields section of the discovery configuration, to generate a chart "
            "of."
        ),
    )
    chart_type: Literal["bar", "choropleth", "histogram", "pie"] = Field(
        ...,
        title="Chart type",
        description="Chart type when displaying. Only one chart type is currently permitted per field.",
    )
    width: int | None = Field(
        default=None,
        ge=1,
        le=3,
        title="Width",
        description=(
            "Initial chart width, in terms of columns. If null/excluded, the front end can decide the initial width."
        ),
    )


class BarChart(BaseOverviewChart):
    chart_type: Literal["bar"] = "bar"


class HistogramChart(BaseOverviewChart):
    chart_type: Literal["histogram"] = "histogram"


class PieChart(BaseOverviewChart):
    chart_type: Literal["pie"] = "pie"


class ChoroplethColorModeContinuous(BaseModel, NoAdditionalProperties):
    mode: Literal["continuous"] = "continuous"
    min_color: str
    max_color: str


# class ChoroplethColorModeDiscrete:
#     mode: Literal["discrete"] = "discrete"
#     # TODO: right now, needs a function, which we cannot support in JSON


class ChoroplethChart(BaseOverviewChart):
    chart_type: Literal["choropleth"] = "choropleth"
    color_mode: ChoroplethColorModeContinuous = Field(
        discriminator="mode",
        title="Color mode",
        description=(
            "Color mode, i.e., method for coloring the choropleth chart. Right now, only `continuous` is supported."
        ),
    )
    center: tuple[float, float] = Field(
        ..., title="Center", description="Choropleth initial map center - latitude and longitude, in decimal degrees."
    )
    zoom: float = Field(..., ge=0, le=15, title="Zoom level", description="Choropleth initial zoom level.")
    category_prop: str = Field(
        ...,
        title="Category property",
        description="GeoJSON polygon property to match against the field value for rendering the choropleth.",
    )
    features: FeatureCollection[Feature[Polygon, dict[str, Any]]] = Field(
        ..., title="Features", description="GeoJSON polygon-only feature collection."
    )


class OverviewChart(RootModel):
    """
    Defines a chart for displaying overview data, including a field, chart type, and additional chart configuration.
    """

    root: BarChart | HistogramChart | PieChart | ChoroplethChart = Field(discriminator="chart_type")

    def __getattr__(self, item):
        return getattr(self.root, item)

    def __setattr__(self, key, value):
        return setattr(self.root, key, value)


class OverviewSection(BaseModel, NoAdditionalProperties):
    """
    Groups charts into a section with a title, e.g., {"section_title": "Demographics", "charts": [{...}, {...}]}
    """

    section_title: str = Field(
        ...,
        title="Section title",
        description="Chart section title, for an overview dashboard or chart management sectioning.",
    )
    charts: list[OverviewChart] = Field(
        ..., title="Charts", description="List of chart definitions contained in the section."
    )
