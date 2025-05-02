import aiohttp
import asyncio
import contextlib

from structlog.stdlib import BoundLogger
from typing import AsyncIterator
from urllib.parse import urljoin

from .types import GA4GHServiceInfo, BentoDataTypeServiceListing, BentoServiceRecord, BentoDataType

__all__ = [
    "ServiceManager",
]


class ServiceManager:
    """
    A class (intended to be a singleton in most circumstances) for interacting with a Bento Service Registry instance.
    Instances provide several methods corresponding to various endpoints of the Bento Service Registry, including for
    accessing Bento service definitions, an aggregation of /service-info endpoints, and service data types.
    """

    def __init__(self, logger: BoundLogger, request_timeout: int, service_registry_url: str, verify_ssl: bool = True):
        self._logger: BoundLogger = logger

        self._service_registry_url: str = service_registry_url.rstrip("/")
        self._timeout: int = request_timeout
        self._verify_ssl: bool = verify_ssl

        self._bento_service_dict: dict[str, BentoServiceRecord] = {}  # dict of {compose ID: service record}
        self._bento_services_by_kind: dict[str, BentoServiceRecord] = {}  # dict of {service kind: service record}
        self._service_list: list[GA4GHServiceInfo] = []
        self._services_by_kind: dict[str, GA4GHServiceInfo] = {}
        self._data_types: dict[str, BentoDataType] = {}  # dict of {data type ID: entry}

    @contextlib.asynccontextmanager
    async def _http_session(
        self,
        existing: aiohttp.ClientSession | None = None,
    ) -> AsyncIterator[aiohttp.ClientSession]:
        # Don't use the FastAPI dependency for the HTTP session, since this object is long-lasting.

        if existing:
            yield existing
            return

        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=self._verify_ssl),
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        try:
            yield session
        finally:
            await session.close()

    async def fetch_bento_services(
        self,
        existing_session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, BentoServiceRecord]:  # dict of {compose ID: service record}
        """
        Fetches Bento service definitions from the Bento Service Registry (the /bento-services endpoint).
        Side effects: populates self._bento_service_dict and self._bento_services_by_kind caches.
        :param existing_session: An existing aiohttp.ClientSession. If left out/None, a new session will be created.
        :param headers: Any headers to forward to the Bento Service Registry instance.
        :return: A dictionary with keys being service Compose IDs and values being BentoServiceRecord-typed
                 dictionaries.
        """

        if self._bento_service_dict:
            return self._bento_service_dict

        session: aiohttp.ClientSession
        async with self._http_session(existing_session) as session:
            url = urljoin(self._service_registry_url, "bento-services")
            async with session.get(url, headers=headers) as r:
                body = await r.json()
                logger = self._logger.bind(bento_services_status=r.status, bento_services_body=body)

                if not r.ok:
                    await logger.aerror("recieved error response from service registry while fetching Bento services")
                    self._bento_service_dict = {}
                    return {}

        bento_services: dict = body
        if bento_services:
            self._bento_service_dict = bento_services
            self._bento_services_by_kind = {s["service_kind"]: s for s in bento_services.values()}
            return bento_services

        await logger.awarning("got empty Bento service response from service registry")
        return {}

    async def get_bento_service_record_by_kind(
        self,
        service_kind: str,
        existing_session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
    ) -> BentoServiceRecord | None:
        """
        Given a Bento service kind, return the Bento service record if one exists.
        Side effects: populates self._bento_service_dict and self._bento_services_by_kind caches.
        :param service_kind: Bento service kind.
        :param existing_session: An existing aiohttp.ClientSession. If left out/None, a new session will be created.
        :param headers: Any headers to forward to the Bento Service Registry instance.
        :return: A BentoServiceRecord-typed dictionary for the specified service kind, if one exists.
        """
        await self.fetch_bento_services(existing_session, headers)
        return self._bento_services_by_kind.get(service_kind)

    async def get_bento_service_url_by_kind(
        self,
        service_kind: str,
        existing_session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
    ) -> str | None:
        """
        Given a Bento service kind, return the base service URL, extracted from a Bento service record if one exists.
        Side effects: populates self._bento_service_dict and self._bento_services_by_kind caches.
        :param service_kind: Bento service kind.
        :param existing_session: An existing aiohttp.ClientSession. If left out/None, a new session will be created.
        :param headers: Any headers to forward to the Bento Service Registry instance.
        :return: Bento service URL, or None if one could not be retrieved.
        """
        sr = await self.get_bento_service_record_by_kind(service_kind, existing_session, headers)
        return sr["url"] if sr is not None else None

    async def fetch_service_list(
        self,
        existing_session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[GA4GHServiceInfo]:
        """
        Fetches a list of service-info responses from Bento services (the /services endpoint of the registry).
        Side effects: populates self._service_list and self._services_by_kind caches.
        :param existing_session: An existing aiohttp.ClientSession. If left out/None, a new session will be created.
        :param headers: Any headers to forward to the Bento Service Registry instance.
        :return: A list of GA4GHServiceInfo-typed dictionaries.
        """

        if self._service_list:
            return self._service_list

        session: aiohttp.ClientSession
        async with self._http_session(existing_session) as session:
            url = urljoin(self._service_registry_url, "services")
            async with session.get(url, headers=headers) as r:
                body = await r.json()
                logger = self._logger.bind(service_list_status=r.status, service_list_body=body)

                if not r.ok:
                    await logger.aerror("recieved error response from service registry while fetching service list")
                    self._service_list = []
                    return []

        service_list: list[GA4GHServiceInfo] = body
        if service_list:
            self._service_list = service_list
            self._services_by_kind = {
                s["bento"]["serviceKind"]: s for s in service_list if s.get("bento", {}).get("serviceKind")
            }
            return service_list

        await logger.awarning("got empty service list response from service registry")
        return []

    async def get_service_info_by_kind(
        self,
        service_kind: str,
        existing_session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
    ) -> GA4GHServiceInfo | None:
        """
        Retrieves a service-info response from a Bento service, given its kind, if one could be found.
        Side effects: populates self._service_list and self._services_by_kind caches.
        :param service_kind: Bento service kind.
        :param existing_session: An existing aiohttp.ClientSession. If left out/None, a new session will be created.
        :param headers: Any headers to forward to the Bento Service Registry instance.
        :return: A GA4GHServiceInfo-typed dictionary, if one could be retrieved for the service kind; otherwise None.
        """
        await self.fetch_service_list(existing_session, headers)  # side effect: populate self._services_by_kind
        return self._services_by_kind.get(service_kind)

    async def fetch_data_types(
        self,
        existing_session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, BentoDataType]:
        """
        Fetches an aggregation of Bento data types, collected from Bento data services' /data-types endpoints.
        Side effects:  populates self._service_list, self._services_by_kind, and self._data_types caches.
        :param existing_session: An existing aiohttp.ClientSession. If left out/None, a new session will be created.
        :param headers: Any headers to forward to the Bento Service Registry instance.
        :return: A dictionary with keys being data type IDs and values being BentoDataType-typed dictionaries.
        """

        if self._data_types:
            return self._data_types

        async def _get_data_types_for_service(
            s: aiohttp.ClientSession, ds: GA4GHServiceInfo
        ) -> tuple[BentoDataType, ...]:
            service_base_url = ds["url"]
            dt_url = service_base_url.rstrip("/") + "/data-types"

            async with s.get(dt_url, headers=headers) as r:
                if not r.ok:
                    await self._logger.aerror(
                        "recieved error from data-types URL", url=dt_url, status=r.status, body=await r.json()
                    )
                    return ()
                service_dts: list[BentoDataTypeServiceListing] = await r.json()

            return tuple(BentoDataType(service_base_url=service_base_url, data_type_listing=sdt) for sdt in service_dts)

        session: aiohttp.ClientSession
        async with self._http_session(existing=existing_session) as session:
            services = await self.fetch_service_list(existing_session=session, headers=headers)
            data_services = [s for s in services if s.get("bento", {}).get("dataService")]

            dts_nested: list[tuple[BentoDataType, ...]] = await asyncio.gather(
                *(_get_data_types_for_service(session, ds) for ds in data_services)
            )

        self._data_types = {dt["data_type_listing"]["id"]: dt for dts_item in dts_nested for dt in dts_item}
        return self._data_types
