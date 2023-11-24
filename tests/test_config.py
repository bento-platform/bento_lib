import logging
import os
import pytest
from bento_lib.config.pydantic import BentoBaseConfig
from bento_lib.service_info.helpers import build_service_info_from_pydantic_config


TEST_CONFIG_VALUES = dict(
    service_id="test",
    service_name="Test",
    bento_authz_service_url="https://authz.local/",
)


def test_base_pydantic_config():
    assert BentoBaseConfig.model_validate(TEST_CONFIG_VALUES).cors_origins == ()
    assert BentoBaseConfig.model_validate(dict(**TEST_CONFIG_VALUES, cors_origins=("*",))).cors_origins == ("*",)
    assert BentoBaseConfig.model_validate(
        dict(**TEST_CONFIG_VALUES, cors_origins=("a", "b"))).cors_origins == ("a", "b")


def test_base_pydantic_config_env():
    try:
        os.environ["CORS_ORIGINS"] = "a;b"
        assert BentoBaseConfig.model_validate(TEST_CONFIG_VALUES).cors_origins == ("a", "b")
    finally:
        os.environ["CORS_ORIGINS"] = ""


@pytest.mark.asyncio
async def test_build_service_info_for_config():
    # Make sure we can build service info from an instance of a Pydantic config with no validation errors
    res = await build_service_info_from_pydantic_config(
        BentoBaseConfig.model_validate(TEST_CONFIG_VALUES),
        logging.getLogger(__name__),
        {"serviceKind": "asdf", "dataService": False},
        {"group": "ca.c3g.bento", "artifact": "beacon", "version": "1.0.0"},
        "1.2.0",
    )
    assert res
