from operator import not_
from typing import Any

from pydantic import Field

from bento_lib.utils.operators import eq_blank, is_none

__all__ = [
    "FIELD_BLANKABLE",
    "FIELD_DICT_OR_EMPTY",
    "FIELD_LIST_OR_EMPTY",
    "FIELD_NULLABLE",
    "field_list_or_empty",
    "field_nullable",
    "field_name_to_camel",
]


FIELD_BLANKABLE = Field(default="", exclude_if=eq_blank)
FIELD_DICT_OR_EMPTY = Field(default_factory=dict, exclude_if=not_)
FIELD_LIST_OR_EMPTY = Field(default_factory=list, exclude_if=not_)
FIELD_NULLABLE = Field(default=None, exclude_if=is_none)


def field_list_or_empty(description: str | None = None) -> Any:
    return Field(default_factory=list, exclude_if=not_, description=description)


def field_nullable(description: str | None = None) -> Any:
    return Field(default=None, exclude_if=is_none, description=description)


def field_name_to_camel(value: str) -> str:
    return "".join(v.capitalize() for i, v in enumerate(value.split("_")) if i > 0)
