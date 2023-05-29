from .base import QueryExecutor
from ..types import QueryRequest, QueryResponse

__all__ = ["QeDataStructure"]


class QeDataStructure(QueryExecutor):
    def execute(self, query_request: QueryRequest) -> QueryResponse:
        pass

    async def execute_async(self, query_request: QueryRequest) -> QueryResponse:
        return self.execute(query_request)  # No asynchronous data structure execution
