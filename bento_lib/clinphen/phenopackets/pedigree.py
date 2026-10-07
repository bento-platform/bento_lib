from typing import Literal

from pydantic import Field

from .._models import BentoClinPhenModel
from .individual import Sex

__all__ = ["AffectedStatus", "Person", "Pedigree"]

type AffectedStatus = Literal["MISSING", "UNAFFECTED", "AFFECTED"]


class Person(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/pedigree.html#person
    """

    family_id: str = Field(..., min_length=1)
    individual_id: str = Field(..., min_length=1)
    paternal_id: str = Field(..., min_length=1)
    maternal_id: str = Field(..., min_length=1)
    sex: Sex
    affected_status: AffectedStatus


class Pedigree(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/pedigree.html#pedigree
    """

    persons: list[Person] = Field(..., min_length=1)
