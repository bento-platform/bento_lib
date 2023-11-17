import bento_lib.service_info as bsi
import logging
import pytest

logger = logging.getLogger(__name__)

service_type: bsi.GA4GHServiceType = {
    "group": "ca.c3g.bento",
    "artifact": "service-registry",
    "version": "1.0.0",
}

service_org: bsi.GA4GHServiceOrganization = {
    "name": "C3G",
    "url": "http://www.computationalgenomics.ca"
}

service_info_dict: bsi.GA4GHServiceInfo = {
    "id": "1",
    "name": "Bento Service Registry",
    "type": service_type,
    "description": "Service registry for a Bento platform node.",
    "organization": service_org,
    "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
    "version": "1.0.0",
    "url": "https://service-registry.example.org",
    "environment": "prod"
}


def test_service_info_pydantic():
    # Should be valid as Pydantic input
    bsi.GA4GhServiceOrganizationModel.model_validate(service_org)


@pytest.mark.asyncio
async def test_service_info_build():
    # Make sure we can build a prod-mode service info dict
    d: bsi.GA4GHServiceInfo = await bsi.build_service_info(service_info_dict, debug=False, local=False, logger=logger)
    assert d["environment"] == bsi.SERVICE_ENVIRONMENT_PROD

    # Make sure we can build a non-local dev-mode service info dict
    d: bsi.GA4GHServiceInfo = await bsi.build_service_info(service_info_dict, debug=True, local=False, logger=logger)
    assert d["environment"] == bsi.SERVICE_ENVIRONMENT_DEV

    # Make sure we can build a local service info dict:

    d: bsi.GA4GHServiceInfo = await bsi.build_service_info(service_info_dict, debug=True, local=True, logger=logger)
    assert d["environment"] == bsi.SERVICE_ENVIRONMENT_DEV
    assert "gitTag" in d["bento"]
    # assert "gitBranch" in d["bento"]  - Isn't present in GitHub CI
    assert "gitCommit" in d["bento"]

    # noinspection PyTypeChecker
    si2: bsi.GA4GHServiceInfo = {**service_info_dict, "bento": {"dataService": True}}
    d: bsi.GA4GHServiceInfo = await bsi.build_service_info(si2, debug=False, local=True, logger=logger)
    assert d["environment"] == bsi.SERVICE_ENVIRONMENT_PROD
    assert "gitTag" in d["bento"]
    # assert "gitBranch" in d["bento"]  - Isn't present in GitHub CI
    assert "gitCommit" in d["bento"]
