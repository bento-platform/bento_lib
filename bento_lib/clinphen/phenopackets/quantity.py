from typing import Self

from pydantic import BaseModel, model_validator

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_NULLABLE

__all__ = ["ReferenceRange", "Quantity"]


class ReferenceRange(BaseModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/reference-range.html
    """

    unit: OntologyClass
    low: float
    high: float

    @model_validator(mode="after")
    def check_high_gte_low(self) -> Self:
        if self.high < self.low:
            raise ValueError("high should not be less than low")
        return self


class Quantity(BaseModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/quantity.html
    """

    unit: OntologyClass
    value: float
    reference_range: ReferenceRange | None = FIELD_NULLABLE
