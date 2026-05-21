from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none

__all__ = ["ReferenceRange", "Quantity"]


class ReferenceRange(BaseModel):
    unit: OntologyClass
    low: float
    high: float


class Quantity(BaseModel):
    unit: OntologyClass
    value: float
    reference_range: ReferenceRange | None = Field(default=None, exclude_if=is_none)
