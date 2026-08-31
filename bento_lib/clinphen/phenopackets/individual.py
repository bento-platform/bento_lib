from datetime import datetime
from typing import Literal

from pydantic import Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none

from .._fields import FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .time_element import TimeElement
from .vital_status import VitalStatus

__all__ = ["KaryotypicSex", "Individual"]

type Sex = Literal["UNKNOWN_SEX", "FEMALE", "MALE", "OTHER_SEX"]

type KaryotypicSex = Literal[
    "UNKNOWN_KARYOTYPE",
    "XX",
    "XY",
    "XO",
    "XXY",
    "XXX",
    "XXYY",
    "XXXY",
    "XXXX",
    "XYY",
    "OTHER_KARYOTYPE",
]


class Individual(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/individual.html
    """

    id: str
    alternate_ids: list[str] = FIELD_LIST_OR_EMPTY  # TODO: format
    date_of_birth: datetime | None = FIELD_NULLABLE
    time_at_last_encounter: TimeElement | None = FIELD_NULLABLE
    vital_status: VitalStatus | None = FIELD_NULLABLE
    sex: Sex | None = FIELD_NULLABLE  # TODO: default to unknown sex?
    karyotypic_sex: KaryotypicSex | None = FIELD_NULLABLE  # TODO: default to unknown karyotype?
    gender: OntologyClass | None = Field(default=None, exclude_if=is_none)
    taxonomy: OntologyClass | None = Field(default=None, exclude_if=is_none)
