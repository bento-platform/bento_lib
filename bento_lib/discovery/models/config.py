from pydantic import BaseModel

from .fields import FieldDefinition
from .overview import OverviewSection
from .search import SearchSection

__all__ = [
    "DiscoveryConfigRules",
    "DiscoveryConfig",
]


class DiscoveryConfigRules(BaseModel):
    count_threshold: int
    max_query_parameters: int


class DiscoveryConfig(BaseModel):
    overview: list[OverviewSection]
    search: list[SearchSection]
    fields: dict[str, FieldDefinition]
    rules: DiscoveryConfigRules
