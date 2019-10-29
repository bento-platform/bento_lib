from datetime import datetime
from typing import Dict, List, Tuple, Union

from . import custom_types
from . import data_structure
from . import postgres

__all__ = [
    "SEARCH_OPERATIONS",
    "SQL_SEARCH_OPERATORS",

    "build_search_response",

    "custom_types",
    "data_structure",
    "postgres"
]


SEARCH_OPERATIONS = ("eq", "lt", "le", "gt", "ge", "co")
SQL_SEARCH_OPERATORS = {
    "eq": "=",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": ">=",
    "co": "LIKE"
}


def build_search_response(results: Union[Dict, List, Tuple], start_time: datetime) -> Dict:
    return {
        "results": results,
        "time": (datetime.now() - start_time).total_seconds()
    }
