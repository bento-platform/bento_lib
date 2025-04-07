from bento_lib.discovery.models import config, overview
from .common import DISCOVERY_CONFIG_PATH


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
    with open(DISCOVERY_CONFIG_PATH, "r") as fh:
        cfg = config.DiscoveryConfig.model_validate_json(fh.read())
