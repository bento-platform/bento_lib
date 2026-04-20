from geojson_pydantic import Polygon, Feature, FeatureCollection
from pydantic import BaseModel, Field, NonNegativeInt, RootModel, conlist
from typing import Any, Literal

from bento_lib.utils.operators import is_not_none
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

FIELD_Y_TITLE = "Field (Y axis)"
FIELD_Y_DESCRIPTION = (
    "Field ID for Y-axis, as defined by a key in the fields section of the discovery configuration. Specified "
    "for certain types of charts (e.g., scatter plots)."
)


class BaseOverviewChart(BaseModel, NoAdditionalProperties):
    # Begin fields for field IDs ---------------------------------------------------------------------------------------
    field: str = Field(
        ...,
        title="Field",
        description=(
            "Field ID, as defined by a key in the fields section of the discovery configuration, to generate a chart "
            "of."
        ),
    )
    field_y: str | None = Field(default=None, title=FIELD_Y_TITLE, description=FIELD_Y_DESCRIPTION)
    field_color: str | None = Field(default=None, title="Field (color)", description="TODO")
    field_style: str | None = Field(default=None, title="Field (style)", description="TODO (shape or line style)")
    field_size: str | None = Field(default=None, title="Field (size)", description="TODO (shape or line size)")
    # End fields for field IDs -----------------------------------------------------------------------------------------
    chart_type: Literal["bar", "choropleth", "geojson", "histogram", "pie"] = Field(
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

    def fields(self) -> tuple[str | None, ...]:
        return self.field, self.field_y, self.field_color, self.field_style, self.field_size

    def set_fields(self) -> tuple[str, ...]:
        return tuple(filter(is_not_none, self.fields()))

    def chart_id(self):
        return "_".join(map(str, filter(is_not_none, (*self.fields(), self.chart_type))))


class BarChart(BaseOverviewChart):
    field_y: None = None
    field_style: None = None
    field_size: None = None
    chart_type: Literal["bar"] = "bar"


class GeoJSONChart(BaseOverviewChart):
    field_y: None = None
    chart_type: Literal["geojson"] = "geojson"


class HeatMapChart(BaseOverviewChart):
    field_color: str = Field(..., title="Field (color)", description="TODO")


class HistogramChart(BaseOverviewChart):
    field_y: None = None
    field_style: None = None
    field_size: None = None
    chart_type: Literal["histogram"] = "histogram"


class PieChart(BaseOverviewChart):
    field_y: None = None
    field_color: None = None
    field_style: None = None
    field_size: None = None
    chart_type: Literal["pie"] = "pie"


class ScatterChart(BaseOverviewChart):
    field_y: str = Field(..., title=FIELD_Y_TITLE, description=FIELD_Y_DESCRIPTION)  # y is mandatory for scatter plots
    chart_type: Literal["scatter"] = "scatter"


class ChoroplethColorModeContinuous(BaseModel, NoAdditionalProperties):
    mode: Literal["continuous"] = "continuous"
    min_color: str
    max_color: str


# class ChoroplethColorModeDiscrete:
#     mode: Literal["discrete"] = "discrete"
#     # TODO: right now, needs a function, which we cannot support in JSON


class ChoroplethChart(BaseOverviewChart):
    chart_type: Literal["choropleth"] = "choropleth"
    field_y: None = None
    field_color: None = None
    field_style: None = None
    field_size: None = None

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

    root: BarChart | ChoroplethChart | GeoJSONChart | HeatMapChart | HistogramChart | PieChart | ScatterChart = Field(
        discriminator="chart_type"
    )

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
    default_charts: conlist(str, min_length=1) | NonNegativeInt | None = Field(
        default=None,
        title="Default charts",
        description=(
            "Which charts (identified by field ID), or how many charts, are displayed by default in the overview "
            "dashboard. If None, the first few charts from this section are displayed by default. If empty, no charts "
            "from this section are displayed by default."
        ),
    )
