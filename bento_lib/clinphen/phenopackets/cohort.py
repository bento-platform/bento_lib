from pydantic import Field

from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY
from .._models import BentoClinPhenExtraPropsModel
from .file import File
from .meta_data import MetaData
from .phenopacket import Phenopacket

__all__ = ["Cohort"]


class Cohort(BentoClinPhenExtraPropsModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/cohort.html
    NOTE: not currently used in Bento
    """

    id: str = Field(..., min_length=1)
    description: str = FIELD_BLANKABLE
    members: list[Phenopacket] = FIELD_LIST_OR_EMPTY
    files: list[File] = FIELD_LIST_OR_EMPTY
    meta_data: MetaData
