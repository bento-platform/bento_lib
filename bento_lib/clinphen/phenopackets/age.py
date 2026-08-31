from pydantic import Field

from .._fields import FIELD_NULLABLE
from .._models import BentoClinPhenModel

__all__ = ["Age", "AgeRange", "GestationalAge"]


class Age(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/age.html
    """
    iso8601duration: str = Field(..., title="ISO8601 Duration")


class AgeRange(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/age.html#agerange
    """
    start: Age
    end: Age


class InnerGestationalAge(BentoClinPhenModel):
    weeks: int
    days: int | None = FIELD_NULLABLE


class GestationalAge(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/gestational-age.html
    """
    gestational_age: InnerGestationalAge = Field(..., alias="gestationalAge")
