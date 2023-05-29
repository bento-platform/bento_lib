from abc import ABC, abstractmethod

from ..types import QueryRequest, QueryResponse

__all__ = [
    "QueryExecutor",
]


class QueryExecutor(ABC):
    @abstractmethod
    def execute(self, query_request: QueryRequest) -> QueryResponse:  # pragma: no cover
        pass

    @abstractmethod
    async def execute_async(self, query_request: QueryRequest) -> QueryResponse:  # pragma: no cover
        pass
