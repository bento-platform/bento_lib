import pytest
from pathlib import Path
from pydantic import ValidationError
from typing import Type

from bento_lib.discovery.exceptions import DiscoveryValidationError
from bento_lib.discovery.helpers import load_discovery_config
from bento_lib.discovery.models import overview

from .common import (
    DISCOVERY_CONFIG_PATH,
    DISCOVERY_CONFIG_INVALID_1_PATH,
    DISCOVERY_CONFIG_INVALID_2_PATH,
    DISCOVERY_CONFIG_INVALID_3_PATH,
    DISCOVERY_CONFIG_INVALID_4_PATH,
    DISCOVERY_CONFIG_INVALID_5_PATH,
)


def test_overview_charts_def():
    m1 = overview.OverviewChart.model_validate(
        {
            "field": "age",
            "chart_type": "histogram",
        }
    )

    assert m1.field == "age"
    assert m1.chart_type == "histogram"

    m2 = overview.OverviewChart.model_validate(
        {
            "field": "map",
            "chart_type": "choropleth",
        }
    )

    assert m2.field == "map"
    assert m2.chart_type == "choropleth"


def test_load_discovery_config():
    cfg = load_discovery_config(DISCOVERY_CONFIG_PATH)
    assert cfg.overview[0].section_title == "General"


@pytest.mark.parametrize(
    "path,exc,exc_str",
    [
        # invalid format (overview is a dict instead of a list)
        (
            DISCOVERY_CONFIG_INVALID_1_PATH,
            ValidationError,
            """1 validation error for DiscoveryConfig
overview
  Input should be a valid array [type=list_type, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/list_type""",
        ),
        # referencing (in overview) a field which doesn't exist:
        (
            DISCOVERY_CONFIG_INVALID_2_PATH,
            DiscoveryValidationError,
            "overview > section Test [0] > age histogram [0]: field definition not found",
        ),
        # referencing (in search) a field which doesn't exist:
        (
            DISCOVERY_CONFIG_INVALID_3_PATH,
            DiscoveryValidationError,
            "search > section Measurements [0] > lab_test_result_value [0]: field definition not found",
        ),
        # duplicate chart
        (
            DISCOVERY_CONFIG_INVALID_4_PATH,
            DiscoveryValidationError,
            "overview > section Measurements [0] > lab_test_result_value histogram [1]: field already seen",
        ),
        # duplicate search field
        (
            DISCOVERY_CONFIG_INVALID_5_PATH,
            DiscoveryValidationError,
            "search > section Measurements [0] > lab_test_result_value [1]: field already seen",
        ),
    ],
)
def test_load_invalid_discovery_configs(path: Path, exc: Type[Exception], exc_str: str):
    with pytest.raises(exc) as e:
        load_discovery_config(path)
    assert str(e.value) == exc_str
