from typing import Union

from .base import QueryExecutor
from ..types import QueryRequest, QueryResponse

__all__ = ["QePostgres"]


class QePostgres(QueryExecutor):
    def __init__(self, query_request: Union[QueryRequest, dict], schema: dict, data_structure=None):
        super().__init__(query_request, schema)
        self._data_structure = data_structure

    def execute(self) -> QueryResponse:
        pass

    async def execute_async(self) -> QueryResponse:
        pass
