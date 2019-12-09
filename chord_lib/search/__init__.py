from datetime import datetime
from typing import Dict, List, Tuple, Union

from . import data_structure
from . import postgres
from . import queries

__all__ = [
    "SEARCH_OP_EQ",
    "SEARCH_OP_LT",
    "SEARCH_OP_LE",
    "SEARCH_OP_GT",
    "SEARCH_OP_GE",
    "SEARCH_OP_CO",
    "SEARCH_OPERATIONS",
    "SEARCH_OPS",
    "SQL_SEARCH_OPERATORS",

    "build_search_response",

    "data_structure",
    "postgres",
    "queries",
]


SEARCH_OP_EQ = "eq"
SEARCH_OP_LT = "lt"
SEARCH_OP_LE = "le"
SEARCH_OP_GT = "gt"
SEARCH_OP_GE = "ge"
SEARCH_OP_CO = "co"

SEARCH_OPERATIONS = (  # TODO: Remove in favour of SEARCH_OPS
    SEARCH_OP_EQ,
    SEARCH_OP_LT,
    SEARCH_OP_LE,
    SEARCH_OP_GT,
    SEARCH_OP_GE,
    SEARCH_OP_CO,
)
SEARCH_OPS = SEARCH_OPERATIONS

SQL_SEARCH_OPERATORS = {
    SEARCH_OP_EQ: "=",
    SEARCH_OP_LT: "<",
    SEARCH_OP_LE: "<=",
    SEARCH_OP_GT: ">",
    SEARCH_OP_GE: ">=",
    SEARCH_OP_CO: "LIKE",
}


def build_search_response(results: Union[Dict, List, Tuple], start_time: datetime) -> Dict:
    return {
        "results": results,
        "time": (datetime.now() - start_time).total_seconds()
    }
