import sys
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from typing_extensions import Self  # TODO: py3.11+ from typing

from ..exceptions import DiscoveryValidationError
from .fields import FieldDefinition
from .overview import OverviewSection
from .search import SearchSection
from ._internal import NoAdditionalProperties

__all__ = [
    "DiscoveryConfigRules",
    "RULES_NO_PERMISSIONS",
    "RULES_FULL_PERMISSIONS",
    "DiscoveryConfigMetadata",
    "DiscoveryConfig",
]

FIELD_DEF_NOT_FOUND = "field definition not found"
FIELD_ALREADY_SEEN = "field already seen"


class DiscoveryConfigRules(BaseModel, NoAdditionalProperties):
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


class DiscoveryConfigMetadata(BaseModel):
    description: str = Field(
        default="", title="Description", description="Optional discovery configuration description."
    )
    authors: list[str] | None = Field(
        default=None,
        title="Authors",
        description="Optional list of authors who wrote this discovery configuration file.",
    )
    timestamp: datetime | None = Field(
        default=None, title="Timestamp", description="Timestamp of when this file was last changed/generated."
    )


# Disallow extra properties at the root level, to prevent mistaken uploads of bad discovery configurations.
# Given that every field has a default, if we didn't do this a completely different JSON just results in an "empty"
# configuration rather than alerting the user that they probably made a mistake.


class DiscoveryConfig(BaseModel, NoAdditionalProperties):
    """
    Configuration for data discovery and visualization within a Bento instance, project, or dataset. Configurable
    aspects include chart display, search fields, and rules for censored count data access.
    """

    # The discovery config version specifies the MAJOR version of the discovery config schema, futureproofing the
    # parsing of discovery config files somewhat.
    version: Literal["1"] = Field(
        default="1", title="Specification version", description="Discovery configuration specification major version"
    )
    # The metadata section (new versus the original JSON schema for "V1" discovery configurations) allows some basic
    # information about who prepared the discovery configuration and when it was generated.
    metadata: DiscoveryConfigMetadata = DiscoveryConfigMetadata()

    overview: list[OverviewSection] = []
    search: list[SearchSection] = []
    fields: dict[str, FieldDefinition] = {}
    rules: DiscoveryConfigRules = Field(
        default=RULES_NO_PERMISSIONS,  # Default rules should be as strict as possible
        title="Discovery rules",
        description="Rules controlling censorship of count responses when a request does not have full data access.",
    )

    @model_validator(mode="after")
    def check_field_references(self) -> Self:
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

    def get_chart_field_ids(self) -> tuple[str, ...]:
        return tuple(chart.field for section in self.overview for chart in section.charts)
