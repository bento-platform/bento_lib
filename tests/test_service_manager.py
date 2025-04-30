import pytest
from aioresponses import aioresponses
from structlog.stdlib import get_logger
from bento_lib.service_info.manager import ServiceManager

logger = get_logger("bento_lib.test")

SR_URL = "https://service-registry.local"


@pytest.fixture(name="service_manager")
def fixt_service_manager():
    return ServiceManager(logger, 60, f"{SR_URL}/", verify_ssl=False)


def test_service_manager_basics(service_manager: ServiceManager):
    assert service_manager._service_registry_url == SR_URL  # ensure we strip the trailing slash
    assert service_manager._timeout == 60
    assert not service_manager._verify_ssl


@pytest.mark.asyncio
async def test_service_manager_bento_services(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(
        f"{SR_URL}/bento-services",
        status=200,
        payload={
            "service-registry": {
                "service_kind": "service-registry",
                "url_template": "{BENTO_PUBLIC_URL}/api/{service_kind}",
                "repository": "git@github.com:bento-platform/bento_service_registry",
                "url": "https://bentov2.local/api/service-registry",
            },
            "drop-box": {
                "service_kind": "drop-box",
                "url_template": "{BENTO_PUBLIC_URL}/api/{service_kind}",
                "repository": "git@github.com:bento-platform/bento_drop_box_service",
                "url": "https://bentov2.local/api/drop-box",
            },
        },
    )

    res = await service_manager.fetch_bento_services()
    assert len(res) == 2
    # TODO

    res = await service_manager.fetch_bento_services()
    # TODO: call again - should use cache


@pytest.mark.asyncio
async def test_service_manager_bento_services_empty(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload={})

    res = await service_manager.fetch_bento_services()
    assert res == {}
    # TODO: assert log warning capture


@pytest.mark.asyncio
async def test_service_manager_bento_services_err(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/bento-services", status=500)

    res = await service_manager.fetch_bento_services()
    assert res == {}
    # TODO: assert log error capture
    # TODO: this should be something else, otherwise we cannot distinguish with true empty response.


def test_service_manager_ga4gh_services(aioresponse: aioresponses):
    # TODO: mock
    pass

    # TODO: call again - should use cache


def test_service_manager_data_types(aioresponse: aioresponses):
    # TODO: mock
    pass

    # TODO: call again - should use cache
