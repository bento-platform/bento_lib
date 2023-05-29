from .base import QueryExecutor
from ..types import QueryRequest, QueryResponse

__all__ = ["QePostgres"]


class QePostgres(QueryExecutor):
    def execute(self, query_request: QueryRequest) -> QueryResponse:
        pass

    async def execute_async(self, query_request: QueryRequest) -> QueryResponse:
        pass
