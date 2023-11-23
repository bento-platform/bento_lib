import asyncio
import copy
import logging

from bento_lib.config.pydantic import BentoBaseConfig
from .constants import SERVICE_ENVIRONMENT_DEV, SERVICE_ENVIRONMENT_PROD
from .types import BentoExtraServiceInfo, GA4GHServiceType, GA4GHServiceOrganization, GA4GHServiceInfo


__all__ = [
    "build_service_info",
    "build_service_info_from_pydantic_config",
]


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


async def build_service_info_from_pydantic_config(
    # dependencies
    config: BentoBaseConfig,
    logger: logging.Logger,
    # values for service info
    bento_service_info: BentoExtraServiceInfo,
    service_type: GA4GHServiceType,
    version: str,
) -> GA4GHServiceInfo:
    desc = config.service_description
    service_org: GA4GHServiceOrganization = config.service_organization.model_dump(mode="json")
    return await build_service_info({
        "id": config.service_id,
        "name": config.service_name,
        "type": service_type,
        **({"description": desc} if desc else {}),
        "organization": service_org,
        "contactUrl": config.service_contact_url,
        "version": version,
        "bento": bento_service_info,
    }, debug=config.bento_debug, local=config.bento_container_local, logger=logger)
