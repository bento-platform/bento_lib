from pydantic import BaseModel, Field
from typing import Literal

__all__ = [
    "OverviewChart",
    "OverviewSection",
]


class OverviewChart(BaseModel):
    field: str = Field(
        ...,
        title="Field",
        description=(
            "Field ID, as defined by a key in the fields section of the discovery configuration, to generate a chart "
            "of."
        ),
    )
    chart_type: Literal["bar", "choropleth", "histogram", "pie"] = Field(..., title="Chart type", description="")


class OverviewSection(BaseModel):
    section_title: str = Field(
        ...,
        title="Section title",
        description="Chart section title, for an overview dashboard or chart management sectioning.",
    )
    charts: list[OverviewChart] = Field(
        ..., title="Charts", description="List of chart definitions contained in the section."
    )
