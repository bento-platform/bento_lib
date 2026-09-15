from pydantic import Field

from .._fields import FIELD_LIST_OR_EMPTY
from .._models import BentoClinPhenExtraPropsModel
from .file import File
from .meta_data import MetaData
from .pedigree import Pedigree
from .phenopacket import Phenopacket

__all__ = ["Family"]


class Family(BentoClinPhenExtraPropsModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/cohort.html
    NOTE: not currently used in Bento
    """

    id: str = Field(..., min_length=1)
    proband: Phenopacket
    relatives: list[Phenopacket] = FIELD_LIST_OR_EMPTY
    consanguinous_parents: bool
    pedigree: Pedigree
    files: list[File] = FIELD_LIST_OR_EMPTY
    meta_data: MetaData
