import json
from pathlib import Path
from pydantic import ValidationError
from structlog.stdlib import BoundLogger

from bento_lib._internal import internal_logger
from .models.config import DiscoveryConfig

__all__ = [
    "load_discovery_config_from_dict",
    "load_discovery_config",
]


FIELD_DEF_NOT_FOUND = "field definition not found"
FIELD_ALREADY_SEEN = "field already seen"


def _warn_for_unreferenced_fields(cfg: DiscoveryConfig, logger: BoundLogger) -> None:
    """
    Issue warnings if there are fields defined that the config doesn't reference.
    :param cfg:
    :param logger: BoundLogger object.
    """

    seen_chart_fields: set[str] = {chart.field for section in cfg.overview for chart in section.charts}
    seen_search_fields: set[str] = {f for section in cfg.search for f in section.fields}
    referenced_fields = seen_chart_fields | seen_search_fields
    for fi, f in enumerate(cfg.fields.keys()):
        if f not in referenced_fields:
            logger.warning("field not referenced", field=f, field_idx=fi)


def load_discovery_config_from_dict(config_data: dict, logger: BoundLogger | None = None) -> DiscoveryConfig:
    # 1. load the config object (or raise a Pydantic validation error if the config is in the wrong format)
    #    the Pydantic model validates the following:
    #     a) make sure all fields in overview and search are defined
    #     b) make sure fields are not listed more than once as a chart or as a search filter
    try:
        cfg = DiscoveryConfig.model_validate(config_data)
    except ValidationError as e:
        raise e

    # 2. validate the config's internal references and overview chart/search field entries
    #  - issue warnings if any fields are defined that the config doesn't reference anywhere
    _warn_for_unreferenced_fields(cfg, logger or internal_logger)

    # TODO: injectable function to validate mapping exists

    return cfg


def load_discovery_config(config_path: Path | str, logger: BoundLogger | None = None) -> DiscoveryConfig:
    with open(config_path, "r") as fh:
        return load_discovery_config_from_dict(json.load(fh), logger)
