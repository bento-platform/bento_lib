from pathlib import Path
from .exceptions import DiscoveryValidationError
from .models.config import DiscoveryConfig

__all__ = [
    "load_discovery_config",
]


def _load_discovery_config_json(config_path: Path | str) -> DiscoveryConfig:
    with open(config_path, "r") as fh:
        return DiscoveryConfig.model_validate_json(fh.read())


def _validate_references_and_duplicates(cfg: DiscoveryConfig) -> None:
    fields = cfg.fields

    # validate overview and check for chart duplicates:
    seen_chart_fields: set[str] = set()
    for s_idx, section in enumerate(cfg.overview):
        for c_idx, chart in enumerate(section.charts):
            exc_path = (
                f"overview > section {section.section_title} [{s_idx}] > {chart.field} {chart.chart_type} [{c_idx}]"
            )
            if chart.field not in fields:
                raise DiscoveryValidationError(f"{exc_path}: field definition not found")
            if chart.field in seen_chart_fields:
                raise DiscoveryValidationError(f"{exc_path}: field already seen")
            seen_chart_fields.add(chart.field)

    # validate search:
    seen_search_fields: set[str] = set()
    for s_idx, section in enumerate(cfg.search):
        for f_idx, f in enumerate(section.fields):
            exc_path = f"search > section {section.section_title} [{s_idx}] > {f} [{f_idx}]"
            if f not in fields:
                raise DiscoveryValidationError(f"{exc_path}: field definition not found")
            if f in seen_search_fields:
                raise DiscoveryValidationError(f"{exc_path}: field already seen")
            seen_search_fields.add(f)


def load_discovery_config(config_path: Path | str) -> DiscoveryConfig:
    # 1. load the config object (or raise a Pydantic validation error if the config is in the wrong format)
    cfg = _load_discovery_config_json(config_path)

    # 2. validate the config's internal references and overview chart/search field entries
    #  a) make sure all fields in overview and search are defined
    #  b) make sure fields are not listed more than once as a chart or as a search filter
    _validate_references_and_duplicates(cfg)

    # now that we've validated references, return the config
    return cfg
