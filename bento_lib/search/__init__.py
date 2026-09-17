from datetime import datetime

from . import data_structure, operations, postgres, queries

__all__ = [
    "build_search_response",
    "data_structure",
    "operations",
    "postgres",
    "queries",
]


def build_search_response(results: dict | list | tuple, start_time: datetime) -> dict:
    return {"results": results, "time": (datetime.now(start_time.tzinfo) - start_time).total_seconds()}
