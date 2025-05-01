import aiohttp
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
    payload = {
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
    }

    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=payload)

    res = await service_manager.fetch_bento_services()
    assert len(res) == 2
    assert res == payload

    res2 = await service_manager.fetch_bento_services()
    assert id(res) == id(res2)  # same dict - cached


@pytest.mark.asyncio
async def test_service_manager_bento_services_empty(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload={})

    res = await service_manager.fetch_bento_services()
    assert res == {}
    assert log_output.entries == [
        {
            "bento_services_body": {},
            "bento_services_status": 200,
            "event": "got empty Bento service response from service registry",
            "log_level": "warning",
        }
    ]


@pytest.mark.asyncio
async def test_service_manager_bento_services_err(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/bento-services", status=500)

    res = await service_manager.fetch_bento_services()
    assert res == {}
    # TODO: assert log error capture
    # TODO: this should be something else, otherwise we cannot distinguish with true empty response.


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services(aioresponse: aioresponses, service_manager: ServiceManager):
    payload = [
        {
            "id": "ca.c3g.bento:edge",
            "name": "Bento Service Registry",
            "type": {"group": "ca.c3g.bento", "artifact": "service-registry", "version": "1.0.0"},
            "organization": {"name": "C3G", "url": "https://www.computationalgenomics.ca"},
            "contactUrl": "mailto:info@c3g.ca",
            "version": "1.5.0",
            "bento": {
                "serviceKind": "service-registry",
                "gitTag": "v1.4.4",
                "gitBranch": "master",
                "gitCommit": "049740e2ebecc27d73070e702a56edf727b67c87",
            },
            "environment": "dev",
            "url": "https://bentov2.local/api/service-registry",
        },
        {
            "id": "ca.c3g.bento:drop-box",
            "name": "Bento Drop Box Service",
            "type": {"group": "ca.c3g.bento", "artifact": "drop-box", "version": "1.1.12"},
            "description": "Drop box service for a Bento platform node.",
            "organization": {"name": "C3G", "url": "https://www.computationalgenomics.ca"},
            "contactUrl": "mailto:info@c3g.ca",
            "version": "1.1.12",
            "bento": {
                "serviceKind": "drop-box",
                "gitRepository": "https://github.com/bento-platform/bento_drop_box_service",
            },
            "environment": "dev",
            "url": "https://bentov2.local/api/drop-box",
        },
    ]

    aioresponse.get(
        f"{SR_URL}/services",
        status=200,
        payload=payload,
    )

    res = await service_manager.fetch_service_list()
    assert len(res) == 2
    assert res == payload

    res2 = await service_manager.fetch_service_list()
    assert id(res) == id(res2)  # same list - cached


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_err(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/services", status=500)

    res = await service_manager.fetch_service_list()
    assert res == []

    assert log_output.entries == [
        {
            "event": "recieved error response from service registry while fetching service " + "list",
            "log_level": "error",
            "service_list_body": None,
            "service_list_status": 500,
        },
    ]


@pytest.mark.asyncio
async def test_service_manager_data_types(aioresponse: aioresponses, service_manager: ServiceManager):
    service_payload = [
        {
            "id": "ca.c3g.chord:metadata",
            "name": "Katsu",
            "type": {"group": "ca.c3g.chord", "artifact": "metadata", "version": "11.0.0"},
            "environment": "dev",
            "description": "Clinical and phenotypic metadata service implementation based on Phenopackets schema.",
            "organization": {"name": "C3G", "url": "https://www.computationalgenomics.ca"},
            "contactUrl": "mailto:info@c3g.ca",
            "version": "11.0.0",
            "bento": {
                "serviceKind": "metadata",
                "dataService": True,
                "gitTag": "v10.0.0",
                "gitBranch": "refact/discovery-config-model",
                "gitCommit": "6862f22c462b8366abacdf42e01a5ddaff173143",
            },
            "url": "https://bentov211.local/api/metadata",
        }
    ]

    dt_payload = [
        {
            "id": "experiment",
            "label": "Experiments",
            "queryable": True,
            "schema": {},
            "metadata_schema": {},
            "count": 4040,
            "last_ingested": "2024-05-22T19:01:49.355649Z",
        }
    ]

    session = aiohttp.ClientSession()

    # repeat=True hack needed for running get() inside asyncio.gather for some reason:
    # https://github.com/pnuckowski/aioresponses/issues/205
    aioresponse.get("https://bentov211.local/api/metadata/data-types", status=200, payload=dt_payload, repeat=True)
    aioresponse.get(f"{SR_URL}/services", status=200, payload=service_payload)

    res = await service_manager.fetch_data_types(existing_session=session)
    assert res == {
        "experiment": {
            "data_type_listing": dt_payload[0],
            "service_base_url": service_payload[0]["url"],
        }
    }

    res2 = await service_manager.fetch_data_types(existing_session=session)
    assert id(res) == id(res2)  # same list - cached
