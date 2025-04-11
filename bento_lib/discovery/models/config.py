import sys
from pydantic import BaseModel, Field, model_validator

from ..exceptions import DiscoveryValidationError
from .fields import FieldDefinition
from .overview import OverviewSection
from .search import SearchSection

__all__ = [
    "DiscoveryConfigRules",
    "RULES_NO_PERMISSIONS",
    "RULES_FULL_PERMISSIONS",
    "DiscoveryConfig",
]


FIELD_DEF_NOT_FOUND = "field definition not found"
FIELD_ALREADY_SEEN = "field already seen"


class DiscoveryConfigRules(BaseModel):
    count_threshold: int = Field(
        ...,
        title="Count threshold",
        description=(
            "If a user has count access and a count is less than or equal to this threshold, it will be censored to 0."
        ),
    )
    max_query_parameters: int = Field(
        ...,
        title="Maximum query parameters",
        description=(
            "If a user has count access, this sets the maximum number of query parameters they can specify when "
            "searching for counts."
        ),
    )


RULES_NO_PERMISSIONS: DiscoveryConfigRules = DiscoveryConfigRules(
    max_query_parameters=0,  # default to no query parameters allowed
    count_threshold=sys.maxsize,  # default to MAXINT count threshold (i.e., no counts can be seen)
)

RULES_FULL_PERMISSIONS: DiscoveryConfigRules = DiscoveryConfigRules(
    max_query_parameters=sys.maxsize,
    count_threshold=0,
)


class DiscoveryConfig(BaseModel):
    overview: list[OverviewSection] = []
    search: list[SearchSection] = []
    fields: dict[str, FieldDefinition] = {}
    rules: DiscoveryConfigRules = RULES_NO_PERMISSIONS  # Default rules should be as strict as possible

    @model_validator(mode="after")
    def check_field_references(self) -> "DiscoveryConfig":
        # validate overview and check for chart duplicates:
        seen_chart_fields: set[str] = set()
        for s_idx, section in enumerate(self.overview):
            for c_idx, chart in enumerate(section.charts):
                exc_path = (
                    f"overview > section {section.section_title} [{s_idx}] > {chart.field} {chart.chart_type} [{c_idx}]"
                )
                log_data = dict(section=section.section_title, field=chart.field, chart_idx=c_idx)
                if chart.field not in self.fields:
                    raise DiscoveryValidationError(FIELD_DEF_NOT_FOUND, exc_path, log_data)
                if chart.field in seen_chart_fields:
                    raise DiscoveryValidationError(FIELD_ALREADY_SEEN, exc_path, log_data)
                seen_chart_fields.add(chart.field)

        # validate search:
        seen_search_fields: set[str] = set()
        for s_idx, section in enumerate(self.search):
            for f_idx, f in enumerate(section.fields):
                exc_path = f"search > section {section.section_title} [{s_idx}] > {f} [{f_idx}]"
                log_data = dict(section=section.section_title, field=f)
                if f not in self.fields:
                    raise DiscoveryValidationError(FIELD_DEF_NOT_FOUND, exc_path, log_data)
                if f in seen_search_fields:
                    raise DiscoveryValidationError(FIELD_ALREADY_SEEN, exc_path, log_data)
                seen_search_fields.add(f)

        return self
