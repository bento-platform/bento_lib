import itertools

from typing import Any, Generator, Set, Tuple, Union

from .base import QueryExecutor
from ..types import QIFilter, QIOr, QueryRequest, QueryResponse

__all__ = ["QeItemList"]


ItemsWithGenerators = Union[dict, float, int, bool, str, Generator[Union[dict, float, int, bool, str], None, None]]
ItemsWithListsAndTuples = Union[dict, float, int, bool, str, list, tuple]


class QeItemList(QueryExecutor):
    def __init__(self, query_request: Union[QueryRequest, dict], schema: dict, items: Tuple[Any] = ()):
        super().__init__(query_request, schema)
        self._items = items

    def execute(self) -> QueryResponse:
        # TODO:
        #  - implicit prefix query with [_root, [item]]
        #  - collect index combinations for queried nested array fields & apply successive filters based on AND.
        #  - peek the queue each time to see if we can short-circuit 0 items.

        root_item_path = ("_root", "[item]")
        array_accesses: Set[Tuple[str, ...]] = {root_item_path}

        def _add_array_accesses_from_filter(f: QIFilter):
            field_path = f.field
            for i in range(len(field_path)):
                if field_path[i] == "[item]":
                    array_accesses.add(("_root", "[item]", *field_path[:i+1]))
            # TODO: process resolves in expr

        for and_term in self.query_request.query.__root__:
            at: Union[QIFilter, QIOr] = and_term.__root__
            if isinstance(at, QIOr):
                for or_term in at.or_field:
                    _add_array_accesses_from_filter(or_term)
            else:  # QIFilter
                _add_array_accesses_from_filter(at)

        root_ds = {"_root": self._items}

        # will sort in nested order, then field order
        #  (a,) (a, c) (a, b, e) (a, b) (a, b, d) will be sorted as
        #  (a,) (a, b) (a, b, d) (a, b, e) (a, c) by default, which is what we want
        array_accesses_sorted = sorted(array_accesses)
        array_accesses_sorted_filtered = []
        last_item = array_accesses_sorted[0]
        for item in array_accesses_sorted[1:]:
            if item[:len(last_item)] != last_item:
                # last_item is not a prefix of this item, so add the last item as the most specific access of
                # that path, and start a new path.
                array_accesses_sorted_filtered.append(item)
            last_item = item
        array_accesses_sorted_filtered.append(last_item)

        def rec_generate_index_combinations(aa: Tuple[str, ...], fixed_indices: dict):
            ds = root_ds
            for (ti, t) in enumerate(aa):
                if t == "[item]":
                    ft = aa[:ti+1]
                    if tuple(ft) in fixed_indices:
                        ds = ds[fixed_indices[ft]]
                    else:
                        # assume we're at the end, and we need to generate index combinations for this item
                        # TODO
                        for vi in range(len(ds)):  # ds should be an array
                            yield from rec_generate_index_combinations(aa, {**fixed_indices, aa: vi})
                else:
                    ds = ds[t]

        index_combinations = list(itertools.chain.from_iterable(
            rec_generate_index_combinations(a, {}) for a in array_accesses_sorted_filtered))

        items_list = []

        # TODO
        
        return QueryResponse(
            result=self.get_response_result_from_list(items_list),
            time=self.get_time(),
        )

    async def execute_async(self) -> QueryResponse:
        return self.execute()  # No asynchronous data structure execution
