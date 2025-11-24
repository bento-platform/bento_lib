import aiohttp
import pytest
from aioresponses import aioresponses
from logging import getLogger
from structlog.stdlib import get_logger
from bento_lib.service_info.manager import ServiceManagerError, ServiceManager

logger = get_logger("bento_lib.test")
std_logger = getLogger("bento_lib.test_std")

SR_URL = "https://test-bento.local/api/service-registry"


@pytest.fixture(name="service_manager")
def fixt_service_manager():
    return ServiceManager(logger, 60, SR_URL, verify_ssl=False)


@pytest.fixture(name="service_manager_std_logger")
def fixt_service_manager_std_logger():
    return ServiceManager(std_logger, 60, SR_URL, verify_ssl=False)


def test_service_manager_basics(service_manager: ServiceManager):
    assert service_manager._service_registry_url == SR_URL + "/"  # ensure we normalize to include the trailing slash
    assert service_manager._timeout == 60
    assert not service_manager._verify_ssl


def test_service_manager_basics_std_logger(service_manager_std_logger: ServiceManager):
    # ensure we normalize to include the trailing slash
    assert service_manager_std_logger._service_registry_url == SR_URL + "/"
    assert service_manager_std_logger._timeout == 60
    assert not service_manager_std_logger._verify_ssl


BENTO_SERVICES_PAYLOAD = {
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


@pytest.mark.asyncio
async def test_service_manager_bento_services(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=BENTO_SERVICES_PAYLOAD)

    res = await service_manager.fetch_bento_services()
    assert len(res) == 2
    assert res == BENTO_SERVICES_PAYLOAD

    res2 = await service_manager.fetch_bento_services()
    assert id(res) == id(res2)  # same dict - cached


@pytest.mark.asyncio
async def test_service_manager_bento_services_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=BENTO_SERVICES_PAYLOAD)

    res = await service_manager_std_logger.fetch_bento_services()
    assert len(res) == 2
    assert res == BENTO_SERVICES_PAYLOAD

    res2 = await service_manager_std_logger.fetch_bento_services()
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
            "log_level": "warning",
            "event": "got empty Bento service response from service registry",
            "bento_services_body": {},
            "bento_services_status": 200,
        }
    ]


@pytest.mark.asyncio
async def test_service_manager_bento_services_err(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/bento-services", status=500)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager.fetch_bento_services()

    assert str(e.value) == "recieved error response from service registry while fetching Bento services"

    assert log_output.entries == [
        {
            "event": "recieved error response from service registry while fetching Bento services",
            "log_level": "error",
            "bento_services_body": None,
            "bento_services_status": 500,
        },
    ]
    # TODO: this should be something else, otherwise we cannot distinguish with true empty response.


@pytest.mark.asyncio
async def test_service_manager_bento_services_by_kind(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=BENTO_SERVICES_PAYLOAD)

    assert (await service_manager.get_bento_service_record_by_kind("service-registry")) == BENTO_SERVICES_PAYLOAD[
        "service-registry"
    ]
    assert (await service_manager.get_bento_service_record_by_kind("drop-box")) == BENTO_SERVICES_PAYLOAD["drop-box"]
    assert (await service_manager.get_bento_service_record_by_kind("does-not-exist")) is None


@pytest.mark.asyncio
async def test_service_manager_bento_services_by_kind_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=BENTO_SERVICES_PAYLOAD)

    assert (
        await service_manager_std_logger.get_bento_service_record_by_kind("service-registry")
    ) == BENTO_SERVICES_PAYLOAD["service-registry"]
    assert (await service_manager_std_logger.get_bento_service_record_by_kind("drop-box")) == BENTO_SERVICES_PAYLOAD[
        "drop-box"
    ]
    assert (await service_manager_std_logger.get_bento_service_record_by_kind("does-not-exist")) is None


@pytest.mark.asyncio
async def test_service_manager_bento_service_urls_by_kind(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=BENTO_SERVICES_PAYLOAD)

    assert (await service_manager.get_bento_service_url_by_kind("service-registry")) == BENTO_SERVICES_PAYLOAD[
        "service-registry"
    ]["url"]
    assert (await service_manager.get_bento_service_url_by_kind("drop-box")) == BENTO_SERVICES_PAYLOAD["drop-box"][
        "url"
    ]
    assert (await service_manager.get_bento_service_url_by_kind("does-not-exist")) is None


@pytest.mark.asyncio
async def test_service_manager_bento_service_urls_by_kind_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/bento-services", status=200, payload=BENTO_SERVICES_PAYLOAD)

    assert (
        await service_manager_std_logger.get_bento_service_url_by_kind("service-registry")
    ) == BENTO_SERVICES_PAYLOAD["service-registry"]["url"]
    assert (await service_manager_std_logger.get_bento_service_url_by_kind("drop-box")) == BENTO_SERVICES_PAYLOAD[
        "drop-box"
    ]["url"]
    assert (await service_manager_std_logger.get_bento_service_url_by_kind("does-not-exist")) is None


SERVICES_PAYLOAD = [
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


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/services", status=200, payload=SERVICES_PAYLOAD, repeat=True)

    res = await service_manager.fetch_service_list()
    assert len(res) == 2
    assert res == SERVICES_PAYLOAD

    res2 = await service_manager.fetch_service_list()
    assert id(res) == id(res2)  # same list - cached

    res3 = await service_manager.fetch_service_list(skip_cache=True)  # force cache re-populate
    assert id(res3) != id(res2)


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/services", status=200, payload=SERVICES_PAYLOAD, repeat=True)

    res = await service_manager_std_logger.fetch_service_list()
    assert len(res) == 2
    assert res == SERVICES_PAYLOAD

    res2 = await service_manager_std_logger.fetch_service_list()
    assert id(res) == id(res2)  # same list - cached

    res3 = await service_manager_std_logger.fetch_service_list(skip_cache=True)  # force cache re-populate
    assert id(res3) != id(res2)


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_by_kind(aioresponse: aioresponses, service_manager: ServiceManager):
    aioresponse.get(f"{SR_URL}/services", status=200, payload=SERVICES_PAYLOAD)

    # check we can get our services by kind, but not a service which doesn't exist
    assert (await service_manager.get_service_info_by_kind("service-registry")) == SERVICES_PAYLOAD[0]
    assert (await service_manager.get_service_info_by_kind("drop-box")) == SERVICES_PAYLOAD[1]
    assert (await service_manager.get_service_info_by_kind("does-not-exist")) is None


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_by_kind_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/services", status=200, payload=SERVICES_PAYLOAD)

    # check we can get our services by kind, but not a service which doesn't exist
    assert (await service_manager_std_logger.get_service_info_by_kind("service-registry")) == SERVICES_PAYLOAD[0]
    assert (await service_manager_std_logger.get_service_info_by_kind("drop-box")) == SERVICES_PAYLOAD[1]
    assert (await service_manager_std_logger.get_service_info_by_kind("does-not-exist")) is None


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_empty(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/services", status=200, payload=[], repeat=True)

    res = await service_manager.fetch_service_list()
    assert res == []

    assert log_output.entries == [
        {
            "log_level": "warning",
            "event": "got empty service list response from service registry",
            "service_list_body": [],
            "service_list_status": 200,
        },
    ]

    assert (await service_manager.get_service_info_by_kind("drop-box")) is None


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_empty_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/services", status=200, payload=[], repeat=True)

    res = await service_manager_std_logger.fetch_service_list()
    assert res == []

    assert (await service_manager_std_logger.get_service_info_by_kind("drop-box")) is None


SERVICE_LIST_LOG_OUTPUT = [
    {
        "log_level": "error",
        "event": "recieved error response from service registry while fetching service list",
        "service_list_body": None,
        "service_list_status": 500,
    },
]


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_err(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/services", status=500)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager.fetch_service_list()

    assert str(e.value) == "recieved error response from service registry while fetching service list"

    assert log_output.entries == SERVICE_LIST_LOG_OUTPUT


@pytest.mark.asyncio
async def test_service_manager_ga4gh_services_err_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/services", status=500)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager_std_logger.fetch_service_list()

    assert str(e.value) == "recieved error response from service registry while fetching service list"


DATA_TYPE_SERVICE_PAYLOAD = [
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


@pytest.mark.asyncio
async def test_service_manager_data_types(aioresponse: aioresponses, service_manager: ServiceManager):
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
    aioresponse.get(f"{SR_URL}/services", status=200, payload=DATA_TYPE_SERVICE_PAYLOAD, repeat=True)

    res = await service_manager.fetch_data_types(existing_session=session)
    assert res == {
        "experiment": {
            "data_type_listing": dt_payload[0],
            "service_base_url": DATA_TYPE_SERVICE_PAYLOAD[0]["url"],
        }
    }

    res2 = await service_manager.fetch_data_types(existing_session=session)
    assert id(res) == id(res2)  # same list - cached

    res3 = await service_manager.fetch_data_types(existing_session=session, skip_cache=True)  # repopulate cache
    assert id(res3) != id(res2)


@pytest.mark.asyncio
async def test_service_manager_data_types_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
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
    aioresponse.get(f"{SR_URL}/services", status=200, payload=DATA_TYPE_SERVICE_PAYLOAD, repeat=True)

    res = await service_manager_std_logger.fetch_data_types(existing_session=session)
    assert res == {
        "experiment": {
            "data_type_listing": dt_payload[0],
            "service_base_url": DATA_TYPE_SERVICE_PAYLOAD[0]["url"],
        }
    }

    res2 = await service_manager_std_logger.fetch_data_types(existing_session=session)
    assert id(res) == id(res2)  # same list - cached

    res3 = await service_manager_std_logger.fetch_data_types(
        existing_session=session, skip_cache=True
    )  # repopulate cache
    assert id(res3) != id(res2)


@pytest.mark.asyncio
async def test_service_manager_data_types_service_err(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    aioresponse.get(f"{SR_URL}/services", status=500)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager.fetch_data_types()

    assert str(e.value) == "recieved error response from service registry while fetching service list"

    assert log_output.entries == SERVICE_LIST_LOG_OUTPUT


@pytest.mark.asyncio
async def test_service_manager_data_types_service_err_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    aioresponse.get(f"{SR_URL}/services", status=500)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager_std_logger.fetch_data_types()

    assert str(e.value) == "recieved error response from service registry while fetching service list"


@pytest.mark.asyncio
async def test_service_manager_data_types_dt_err(
    aioresponse: aioresponses, service_manager: ServiceManager, log_output
):
    # repeat=True hack needed for running get() inside asyncio.gather for some reason:
    # https://github.com/pnuckowski/aioresponses/issues/205
    aioresponse.get("https://bentov211.local/api/metadata/data-types", status=500, repeat=True)
    aioresponse.get(f"{SR_URL}/services", status=200, payload=DATA_TYPE_SERVICE_PAYLOAD)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager.fetch_data_types()

    assert str(e.value) == "recieved error from data-types URL"

    assert log_output.entries == [
        {
            "log_level": "error",
            "event": "recieved error from data-types URL",
            "url": "https://bentov211.local/api/metadata/data-types",
            "status": 500,
            "body": None,
        },
    ]


@pytest.mark.asyncio
async def test_service_manager_data_types_dt_err_std_logger(
    aioresponse: aioresponses, service_manager_std_logger: ServiceManager
):
    # repeat=True hack needed for running get() inside asyncio.gather for some reason:
    # https://github.com/pnuckowski/aioresponses/issues/205
    aioresponse.get("https://bentov211.local/api/metadata/data-types", status=500, repeat=True)
    aioresponse.get(f"{SR_URL}/services", status=200, payload=DATA_TYPE_SERVICE_PAYLOAD)

    with pytest.raises(ServiceManagerError) as e:
        await service_manager_std_logger.fetch_data_types()

    assert str(e.value) == "recieved error from data-types URL"
