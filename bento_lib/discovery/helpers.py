import json
from pathlib import Path
from pydantic import ValidationError
from structlog.stdlib import BoundLogger

from bento_lib._internal import internal_logger
from .models.config import DiscoveryConfig
from .types import WarningsTuple

__all__ = [
    "load_discovery_config_from_dict",
    "load_discovery_config",
]


FIELD_DEF_NOT_FOUND = "field definition not found"
FIELD_ALREADY_SEEN = "field already seen"


def _warn_for_unreferenced_fields(cfg: DiscoveryConfig, logger: BoundLogger) -> WarningsTuple:
    """
    Issue warnings if there are fields defined that the config doesn't reference.
    :param cfg: A DiscoveryConfig instance to check/warn for unreferenced field issues.
    :param logger: BoundLogger object.
    :return: A tuple of warning tuples, which are of the shape (index or path to warning location, warning message).
    """

    warnings: list[tuple[tuple[int | str, ...], str]] = []

    seen_chart_fields: set[str] = {chart.field for section in cfg.overview for chart in section.charts}
    seen_search_fields: set[str] = {f for section in cfg.search for f in section.fields}
    referenced_fields = seen_chart_fields | seen_search_fields
    for fi, f in enumerate(cfg.fields.keys()):
        if f not in referenced_fields:
            logger.warning("field not referenced", field=f, field_idx=fi)
            warnings.append(((fi,), f"field not referenced (field={f})"))

    return tuple(warnings)


def load_discovery_config_from_dict(
    config_data: dict, logger: BoundLogger | None = None
) -> tuple[DiscoveryConfig, WarningsTuple]:
    """
    Load and validate a discovery configuration object from a (presumably) Pydantic-compatible dictionary.
    :param config_data: A Python dictionary to be validated and converted into a DiscoveryConfig instance.
    :param logger: A structlog.stdlib.BoundLogger object, or None to use the bento_lib internal logger.
    :return: A tuple of (instance of the DiscoveryConfig Pydantic model, tuple of warnings).
    """

    # 1. load the config object (or raise a Pydantic validation error if the config is in the wrong format)
    #    the Pydantic model validates the following:
    #     a) make sure all fields in overview and search are defined
    #     b) make sure fields are not listed more than once as a chart or as a search filter
    try:
        cfg = DiscoveryConfig.model_validate(config_data)
    except ValidationError as e:
        raise e

    # 2. validate the config's internal references and overview chart/search field entries
    #  - issue and collect warnings if any fields are defined that the config doesn't reference anywhere
    warnings = _warn_for_unreferenced_fields(cfg, logger or internal_logger)

    # TODO: injectable function to validate mapping exists?

    return cfg, warnings


def load_discovery_config(
    config_path: Path | str, logger: BoundLogger | None = None
) -> tuple[DiscoveryConfig, WarningsTuple]:
    """
    Load and validate a discovery configuration object from a JSON file path.
    :param config_path: The path to the JSON file to load and validate.
    :param logger: A structlog.stdlib.BoundLogger object, or None to use the bento_lib internal logger.
    :return: A tuple of (instance of the DiscoveryConfig Pydantic model, tuple of warnings).
    """
    with open(config_path, "r") as fh:
        return load_discovery_config_from_dict(json.load(fh), logger)
