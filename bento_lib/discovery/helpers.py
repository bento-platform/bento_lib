from pathlib import Path
from structlog.stdlib import BoundLogger

from bento_lib._internal import internal_logger
from .exceptions import DiscoveryValidationError
from .models.config import DiscoveryConfig

__all__ = [
    "load_discovery_config",
]


FIELD_DEF_NOT_FOUND = "field definition not found"
FIELD_ALREADY_SEEN = "field already seen"


def _load_discovery_config_json(config_path: Path | str) -> DiscoveryConfig:
    with open(config_path, "r") as fh:
        return DiscoveryConfig.model_validate_json(fh.read())


def _validate_references_and_duplicates(cfg: DiscoveryConfig, logger: BoundLogger) -> None:
    fields = cfg.fields

    # validate overview and check for chart duplicates:
    seen_chart_fields: set[str] = set()
    for s_idx, section in enumerate(cfg.overview):
        for c_idx, chart in enumerate(section.charts):
            exc_path = (
                f"overview > section {section.section_title} [{s_idx}] > {chart.field} {chart.chart_type} [{c_idx}]"
            )
            if chart.field not in fields:
                logger.error(
                    f"overview {FIELD_DEF_NOT_FOUND}", section=section.section_title, field=chart.field, chart_idx=c_idx
                )
                raise DiscoveryValidationError(f"{exc_path}: {FIELD_DEF_NOT_FOUND}")
            if chart.field in seen_chart_fields:
                logger.error(
                    f"overview {FIELD_ALREADY_SEEN}", section=section.section_title, field=chart.field, chart_idx=c_idx
                )
                raise DiscoveryValidationError(f"{exc_path}: {FIELD_ALREADY_SEEN}")
            seen_chart_fields.add(chart.field)

    # validate search:
    seen_search_fields: set[str] = set()
    for s_idx, section in enumerate(cfg.search):
        for f_idx, f in enumerate(section.fields):
            exc_path = f"search > section {section.section_title} [{s_idx}] > {f} [{f_idx}]"
            if f not in fields:
                logger.error(f"search {FIELD_DEF_NOT_FOUND}", section=section.section_title, field=f)
                raise DiscoveryValidationError(f"{exc_path}: {FIELD_DEF_NOT_FOUND}")
            if f in seen_search_fields:
                logger.error(f"search {FIELD_ALREADY_SEEN}", section=section.section_title, field=f)
                raise DiscoveryValidationError(f"{exc_path}: {FIELD_ALREADY_SEEN}")
            seen_search_fields.add(f)

    # issue warnings if there are fields defined that the config doesn't reference:
    referenced_fields = seen_chart_fields | seen_search_fields
    for fi, f in enumerate(fields.keys()):
        if f not in referenced_fields:
            logger.warning("field not referenced", field=f, field_idx=fi)


def load_discovery_config(config_path: Path | str, logger: BoundLogger | None = None) -> DiscoveryConfig:
    # 1. load the config object (or raise a Pydantic validation error if the config is in the wrong format)
    cfg = _load_discovery_config_json(config_path)

    # 2. validate the config's internal references and overview chart/search field entries
    #  a) make sure all fields in overview and search are defined
    #  b) make sure fields are not listed more than once as a chart or as a search filter
    #  c) issue warnings if any fields are defined that the config doesn't reference anywhere
    _validate_references_and_duplicates(cfg, logger or internal_logger)

    # now that we've validated references, return the config
    return cfg
