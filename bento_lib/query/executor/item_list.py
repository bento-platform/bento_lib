from typing import Any, Generator, Tuple, Union

from .base import QueryExecutor
from ..types import QueryRequest, QueryResponse

__all__ = ["QeItemList"]


ItemsWithGenerators = Union[dict, float, int, bool, str, Generator[Union[dict, float, int, bool, str], None, None]]
ItemsWithListsAndTuples = Union[dict, float, int, bool, str, list, tuple]


class QeItemList(QueryExecutor):
    def __init__(self, query_request: Union[QueryRequest, dict], schema: dict, items: Tuple[Any] = ()):
        super().__init__(query_request, schema)
        self._items = items

    def _item_to_generators_rec(self, item: ItemsWithListsAndTuples) -> ItemsWithGenerators:
        if isinstance(item, dict):
            return {
                k: self._item_to_generators_rec(v)
                for k, v in item.values()
            }
        elif isinstance(item, list) or isinstance(item, tuple):  # TODO: py3.10: union isinstance syntax
            return (self._item_to_generators_rec(v) for v in item)
        else:
            return item  # primitive base case

    def _resolve_generators_rec(self, item: ItemsWithGenerators) -> ItemsWithListsAndTuples:
        if isinstance(item, dict):
            return {
                k: self._resolve_generators_rec(v)
                for k, v in item.values()
            }

    def execute(self) -> QueryResponse:
        # TODO:
        #  - get all array subfields being accessed to know what we are filtering
        #  - start with a generator of all items
        #  - add in generator filters for each AND
        #  - at the end, resolve items, filtering nested arrays if the query item applies to it

        items_gen = self._item_to_generators_rec(self._items)

        # TODO

        items_list = list(items_gen)  # TODO: nested resolve generators
        return QueryResponse(
            result=self.get_response_result_from_list(items_list),
            time=self.get_time(),
        )

    async def execute_async(self) -> QueryResponse:
        return self.execute()  # No asynchronous data structure execution
