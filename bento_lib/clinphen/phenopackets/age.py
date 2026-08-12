from pydantic import BaseModel, Field
from bento_lib.utils.operators import is_none

__all__ = ["Age", "AgeRange", "GestationalAge"]


class Age(BaseModel):
    iso8601duration: str = Field(..., title="ISO8601 Duration")


class AgeRange(BaseModel):
    start: Age
    end: Age


class InnerGestationalAge(BaseModel):
    weeks: int
    days: int | None = Field(default=None, exclude_if=is_none)


class GestationalAge(BaseModel):
    gestational_age: InnerGestationalAge = Field(..., alias="gestationalAge")
