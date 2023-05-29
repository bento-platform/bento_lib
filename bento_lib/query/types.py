from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Union


# TODO: operator
# TODO: Expr type


FieldPath = List[str]
Expr = Any


class QIFilter(BaseModel):
    field: FieldPath
    negated: bool = False
    operator: Literal["="]  # Need to type-check whether operator works against expr
    expr: Union[Expr, List[int], List[float], int, float, str, bool]


class QIOr(BaseModel):
    or_field: List[QIFilter] = Field(..., alias="or")


class QueryItem(BaseModel):
    __root__ = Union[QIFilter, QIOr]


class Query(BaseModel):
    __root__ = List[QueryItem]


class QueryRequestResponseSpec(BaseModel):
    type: Literal["boolean", "count", "items"]
    item: Union[FieldPath, Dict[str, Any], None] = None
    key: Union[str, None] = None


class QueryRequest(BaseModel):
    query: Query
    response: QueryRequestResponseSpec


class QueryResponse(BaseModel):
    result: Union[bool, int, List[dict]]
    time: float
