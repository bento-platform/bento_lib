import logging
import os
import pytest
from bento_lib.config.pydantic import BentoBaseConfig, BentoFastAPIBaseConfig
from bento_lib.service_info.helpers import build_service_info_from_pydantic_config
from bento_lib.service_info.types import BentoExtraServiceInfo, GA4GHServiceType

TEST_CONFIG_VALUES = dict(
    service_id="test",
    service_name="Test",
    bento_authz_service_url="https://authz.local/",
)

TEST_BENTO_SERVICE_INFO: BentoExtraServiceInfo = {"serviceKind": "asdf", "dataService": False}
TEST_SERVICE_TYPE: GA4GHServiceType = {"group": "ca.c3g.bento", "artifact": "beacon", "version": "1.0.0"}


def test_base_pydantic_config():
    assert BentoBaseConfig.model_validate(TEST_CONFIG_VALUES).cors_origins == ()
    assert BentoBaseConfig.model_validate(dict(**TEST_CONFIG_VALUES, cors_origins=("*",))).cors_origins == ("*",)
    assert BentoBaseConfig.model_validate(dict(**TEST_CONFIG_VALUES, cors_origins=("a", "b"))).cors_origins == (
        "a",
        "b",
    )


def test_base_pydantic_config_env():
    try:
        os.environ["CORS_ORIGINS"] = "a;b"
        assert BentoBaseConfig.model_validate(TEST_CONFIG_VALUES).cors_origins == ("a", "b")
    finally:
        os.environ["CORS_ORIGINS"] = ""


def test_fastapi_pydantic_config():
    assert BentoFastAPIBaseConfig.model_validate(TEST_CONFIG_VALUES).service_docs_path == "/docs"

    try:
        os.environ["SERVICE_DOCS_PATH"] = "/docs-alt"
        assert BentoFastAPIBaseConfig.model_validate(TEST_CONFIG_VALUES).service_docs_path == "/docs-alt"
    finally:
        os.environ["SERVICE_DOCS_PATH"] = ""


@pytest.mark.asyncio
async def test_build_service_info_for_config():
    # Make sure we can build service info from an instance of a Pydantic config with no validation errors
    res = await build_service_info_from_pydantic_config(
        BentoBaseConfig.model_validate(TEST_CONFIG_VALUES),
        logging.getLogger(__name__),
        TEST_BENTO_SERVICE_INFO,
        TEST_SERVICE_TYPE,
        "1.2.0",
    )
    assert res


@pytest.mark.asyncio
async def test_build_service_info_for_config_with_description():
    # Same as above, but with a service description set
    desc = "This is a pretend service"
    res = await build_service_info_from_pydantic_config(
        BentoBaseConfig.model_validate({**TEST_CONFIG_VALUES, "service_description": desc}),
        logging.getLogger(__name__),
        TEST_BENTO_SERVICE_INFO,
        TEST_SERVICE_TYPE,
        "1.2.0",
    )
    assert res["description"] == desc
