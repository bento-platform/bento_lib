from operator import not_
from pydantic import Field
from bento_lib.utils.operators import eq_blank, is_none

__all__ = [
    "FIELD_BLANKABLE",
    "FIELD_LIST_OR_EMPTY",
    "FIELD_NULLABLE",
]


FIELD_BLANKABLE = Field(default="", exclude_if=eq_blank)
FIELD_LIST_OR_EMPTY = Field(default_factory=list, exclude_if=not_)
FIELD_NULLABLE = Field(default=None, exclude_if=is_none)
