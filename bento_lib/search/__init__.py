from datetime import datetime
from typing import Dict, List, Tuple, Union

from . import data_structure
from . import operations
from . import postgres
from . import queries

__all__ = [
    "build_search_response",
    "data_structure",
    "operations",
    "postgres",
    "queries",
]


def build_search_response(results: Union[Dict, List, Tuple], start_time: datetime) -> Dict:
    return {"results": results, "time": (datetime.now() - start_time).total_seconds()}
