import pytest
import sys
from pathlib import Path
from pydantic import ValidationError
from typing import Type

from bento_lib.discovery.helpers import load_discovery_config_from_dict, load_discovery_config
from bento_lib.discovery.models import fields, overview

from .common import (
    DISCOVERY_CONFIG_PATH,
    DISCOVERY_CONFIG_INVALID_1_PATH,
    DISCOVERY_CONFIG_INVALID_2_PATH,
    DISCOVERY_CONFIG_INVALID_3_PATH,
    DISCOVERY_CONFIG_INVALID_4_PATH,
    DISCOVERY_CONFIG_INVALID_5_PATH,
    DISCOVERY_CONFIG_WARNING_PATH,
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


def test_load_discovery_config_dict():
    cfg = load_discovery_config_from_dict(
        {
            "overview": [
                {
                    "section_title": "General",
                    "charts": [
                        {"field": "age", "chart_type": "histogram"},
                    ],
                }
            ],
            "search": [
                {
                    "section_title": "General",
                    "fields": [
                        "age",
                    ],
                },
            ],
            "fields": {
                "age": {
                    "mapping": "individual/age_numeric",
                    "title": "Age",
                    "description": "Age at arrival",
                    "datatype": "number",
                    "config": {
                        "bin_size": 10,
                        "taper_left": 10,
                        "taper_right": 100,
                        "units": "years",
                        "minimum": 0,
                        "maximum": 100,
                    },
                },
            },
            "rules": {"count_threshold": 5, "max_query_parameters": 2},
        }
    )

    assert len(cfg.overview) == 1
    assert len(cfg.search) == 1
    assert len(cfg.fields) == 1
    assert cfg.rules.count_threshold == 5


def test_load_discovery_config_dict_blank():
    cfg = load_discovery_config_from_dict({})
    assert cfg.overview == []
    assert cfg.search == []
    assert cfg.fields == {}
    assert cfg.rules.max_query_parameters == 0
    assert cfg.rules.count_threshold == sys.maxsize


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
  Input should be a valid list [type=list_type, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/list_type""",
        ),
        # referencing (in overview) a field which doesn't exist:
        (
            DISCOVERY_CONFIG_INVALID_2_PATH,
            ValidationError,
            "overview > section Test [0] > age histogram [0] [type=field definition not found",
        ),
        # referencing (in search) a field which doesn't exist:
        (
            DISCOVERY_CONFIG_INVALID_3_PATH,
            ValidationError,
            "search > section Measurements [0] > lab_test_result_value [0] [type=field definition not found",
        ),
        # duplicate chart
        (
            DISCOVERY_CONFIG_INVALID_4_PATH,
            ValidationError,
            "overview > section Measurements [0] > lab_test_result_value histogram [1] [type=field already seen",
        ),
        # duplicate search field
        (
            DISCOVERY_CONFIG_INVALID_5_PATH,
            ValidationError,
            "search > section Measurements [0] > lab_test_result_value [1] [type=field already seen",
        ),
    ],
)
def test_load_invalid_discovery_configs(path: Path, exc: Type[Exception], exc_str: str):
    with pytest.raises(exc) as e:
        load_discovery_config(path)
    assert exc_str in str(e.value)


def test_discovery_config_warning(log_output):
    load_discovery_config(DISCOVERY_CONFIG_WARNING_PATH)
    assert log_output.entries == [
        {"field": "lab_test_result_value", "field_idx": 0, "event": "field not referenced", "log_level": "warning"}
    ]


TEST_NUMBER_FIELD_BASE = {
    "mapping": "whatever/test",
    "title": "Test",
    "description": "test",
    "data_type": "number",
    "config": {
        "units": "m",
    },
}


@pytest.mark.parametrize(
    "partial_config,err_str",
    [
        # manual bin configs --------------------------------------------------
        (
            # 'swapped' maximum/minimum (max cannot be < min)
            {"bins": [10, 20, 30], "maximum": 5, "minimum": 40},
            "Value error, maximum cannot be less than minimum",
        ),
        (
            # minimum > bins[0]:
            {"bins": [10, 20, 30], "minimum": 15, "maximum": 40},
            "Value error, minimum cannot be greater than first bin",
        ),
        (
            # maximum < bins[-1]:
            {"bins": [10, 20, 30], "minimum": 5, "maximum": 25},
            "Value error, maximum cannot be less than last bin",
        ),
        # automatic bin configs -----------------------------------------------
        (
            # 'swapped' maximum/minimum (max cannot be < min)
            {
                "bin_size": 5,
                "taper_left": 10,
                "taper_right": 90,
                "minimum": 100,
                "maximum": 0,
            },
            "Value error, maximum cannot be less than minimum",
        ),
        (
            # 'swapped' taper left/taper right
            {
                "bin_size": 5,
                "taper_left": 90,
                "taper_right": 10,
                "minimum": 0,
                "maximum": 100,
            },
            "Value error, taper_right cannot be less than taper_left",
        ),
        (
            # taper_left < min
            {
                "bin_size": 5,
                "taper_left": 0,
                "taper_right": 90,
                "minimum": 10,
                "maximum": 100,
            },
            "Value error, taper_left cannot be less than minimum",
        ),
        (
            # taper_right > max
            {
                "bin_size": 5,
                "taper_left": 10,
                "taper_right": 100,
                "minimum": 0,
                "maximum": 90,
            },
            "Value error, taper_right cannot be greater than maximum",
        ),
        (
            # taper value range not divisible by bin size
            {
                "bin_size": 5,
                "taper_left": 10,
                "taper_right": 93,
                "minimum": 0,
                "maximum": 100,
            },
            "Value error, range between taper values is not a multiple of bin_size",
        ),
    ],
)
def test_invalid_number_configs(partial_config, err_str: str):
    with pytest.raises(ValidationError) as e:
        fields.NumberFieldDefinition.model_validate(
            {
                **TEST_NUMBER_FIELD_BASE,
                "config": {**TEST_NUMBER_FIELD_BASE["config"], **partial_config},
            }
        )

    assert e.value.error_count() == 1
    assert err_str in str(e.value)
