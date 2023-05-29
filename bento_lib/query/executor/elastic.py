from .base import QueryExecutor
from ..types import QueryResponse

__all__ = ["QeElastic"]


class QeElastic(QueryExecutor):
    def execute(self) -> QueryResponse:
        pass

    async def execute_async(self) -> QueryResponse:
        pass
