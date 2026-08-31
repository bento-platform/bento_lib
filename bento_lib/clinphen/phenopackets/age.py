from pydantic import Field

from .._fields import FIELD_NULLABLE
from .._models import BentoClinPhenModel

__all__ = ["Age", "AgeRange", "GestationalAge"]


class Age(BentoClinPhenModel):
    iso8601duration: str = Field(..., title="ISO8601 Duration")


class AgeRange(BentoClinPhenModel):
    start: Age
    end: Age


class InnerGestationalAge(BentoClinPhenModel):
    weeks: int
    days: int | None = FIELD_NULLABLE


class GestationalAge(BentoClinPhenModel):

    gestational_age: InnerGestationalAge = Field(..., alias="gestationalAge")
