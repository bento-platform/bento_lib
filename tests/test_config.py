import os
from bento_lib.config.pydantic import BentoBaseConfig


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
