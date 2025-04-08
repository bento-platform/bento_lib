from pydantic import BaseModel
from typing import Literal

__all__ = [
    "OverviewChart",
    "OverviewSection",
]


class OverviewChart(BaseModel):
    field: str
    chart_type: Literal["bar", "choropleth", "histogram", "pie"]


class OverviewSection(BaseModel):
    section_title: str
    charts: list[OverviewChart]
