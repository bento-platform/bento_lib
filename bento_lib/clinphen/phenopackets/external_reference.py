from typing import Self

from pydantic import model_validator

from .._fields import FIELD_BLANKABLE
from .._models import BentoClinPhenModel

__all__ = ["ExternalReference"]


class ExternalReference(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/externalreference.html
    """

    id: str = FIELD_BLANKABLE
    reference: str = FIELD_BLANKABLE
    description: str = FIELD_BLANKABLE

    @model_validator(mode="after")
    def check_at_least_one(self) -> Self:
        if not any((self.id, self.reference, self.description)):
            raise ValueError("external reference should have at least one value")
        return self
