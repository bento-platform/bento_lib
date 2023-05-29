from abc import ABC, abstractmethod
from datetime import datetime
from typing import Union

from ..types import QueryRequest, QueryResponse

__all__ = [
    "QueryExecutor",
]


class QueryExecutor(ABC):
    def __init__(self, query_request: Union[QueryRequest, dict], search_schema: dict, **kwargs):
        self._query_request: QueryRequest = (
            query_request if isinstance(query_request, QueryRequest) else QueryRequest.parse_obj(query_request))
        self._search_schema: dict = search_schema
        self._start_time: datetime = datetime.now()

    def get_time(self) -> float:
        return (datetime.now() - self._start_time).total_seconds()

    def get_response_result_from_list(self, items: list) -> Union[bool, int, list]:
        qr = self.query_request
        return (
            len(items) > 0 if qr.response.type == "boolean"
            else (
                len(items) if qr.response.type == "count"
                else []
            )
        )

    def empty_response(self) -> QueryResponse:
        return QueryResponse(
            result=self.get_response_result_from_list([]),
            time=self.get_time()
        )

    @property
    def query_request(self) -> QueryRequest:
        return self._query_request

    @abstractmethod
    def execute(self) -> QueryResponse:  # pragma: no cover
        pass

    @abstractmethod
    async def execute_async(self) -> QueryResponse:  # pragma: no cover
        pass
