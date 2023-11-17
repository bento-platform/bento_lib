import asyncio
import copy
import logging

from pydantic import BaseModel, ConfigDict
from typing import Literal, TypedDict

__all__ = [
    "GA4GHServiceType",
    "GA4GHServiceOrganization",
    "GA4GhServiceOrganizationModel",
    "SERVICE_ORGANIZATION_C3G",
    "SERVICE_ORGANIZATION_C3G_PYDANTIC",
    "BentoExtraServiceInfo",
    "GA4GHServiceInfo",
    "SERVICE_ENVIRONMENT_DEV",
    "SERVICE_ENVIRONMENT_PROD",
    "build_service_info",
]


class GA4GHServiceType(TypedDict):
    group: str
    artifact: str
    version: str


class GA4GHServiceOrganization(TypedDict):
    name: str
    url: str


class GA4GhServiceOrganizationModel(BaseModel):
    name: str
    url: str
    model_config = ConfigDict(extra="forbid")


SERVICE_ORGANIZATION_C3G: GA4GHServiceOrganization = {"name": "C3G", "url": "https://www.computationalgenomics.ca"}
SERVICE_ORGANIZATION_C3G_PYDANTIC: GA4GhServiceOrganizationModel = GA4GhServiceOrganizationModel.model_validate(
    SERVICE_ORGANIZATION_C3G)


# TODO: py3.11: Required[] instead of base class


class BentoExtraServiceInfo(TypedDict, total=False):
    serviceKind: str  # One service_kind per Bento service/instance
    dataService: bool  # Whether the service provides data types/search/workflows
    # Whether the service provides workflows:
    #   - not necessarily data types; split from dataService to allow services to provide workflows
    #     without needing to provide data types/search endpoints as well
    #   - implict default: false
    workflowProvider: bool
    # Git information: only added if we're in a local development mode
    gitRepository: str
    gitTag: str
    gitBranch: str
    gitCommit: str


class _GA4GHServiceInfoBase(TypedDict):
    id: str
    name: str
    type: GA4GHServiceType
    organization: GA4GHServiceOrganization
    version: str


class GA4GHServiceInfo(_GA4GHServiceInfoBase, total=False):
    description: str
    contactUrl: str
    documentationUrl: str
    url: str  # Technically not part of spec; comes from service-registry
    environment: Literal["dev", "prod"]
    # Bento-specific service info properties are contained inside a nested, "bento"-keyed dictionary
    bento: BentoExtraServiceInfo


SERVICE_ENVIRONMENT_DEV: Literal["dev"] = "dev"
SERVICE_ENVIRONMENT_PROD: Literal["prod"] = "prod"


async def _git_stdout(*args) -> str:
    git_proc = await asyncio.create_subprocess_exec(
        "git", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    res, _ = await git_proc.communicate()
    return res.decode().rstrip()


async def build_service_info(
    base_service_info: GA4GHServiceInfo,
    debug: bool,
    local: bool,
    logger: logging.Logger,
) -> GA4GHServiceInfo:
    service_info_dict: GA4GHServiceInfo = copy.deepcopy(base_service_info)
    service_info_dict["environment"] = SERVICE_ENVIRONMENT_DEV if debug else SERVICE_ENVIRONMENT_PROD

    if not local:
        return service_info_dict

    try:
        res_tag, res_branch, res_commit = await asyncio.gather(
            _git_stdout("describe", "--tags", "--abbrev=0"),
            _git_stdout("branch", "--show-current"),
            _git_stdout("rev-parse", "HEAD"),
        )

        if "bento" not in service_info_dict:
            service_info_dict["bento"] = {}

        if res_tag:  # pragma: no cover
            # noinspection PyTypeChecker
            service_info_dict["bento"]["gitTag"] = res_tag
        if res_branch:  # pragma: no cover
            # noinspection PyTypeChecker
            service_info_dict["bento"]["gitBranch"] = res_branch
        if res_commit:  # pragma: no cover
            # noinspection PyTypeChecker
            service_info_dict["bento"]["gitCommit"] = res_commit

    except Exception as e:  # pragma: no cover
        except_name = type(e).__name__
        logger.error(f"Error retrieving git information: {str(except_name)}")

    return service_info_dict  # updated service info with the git info
