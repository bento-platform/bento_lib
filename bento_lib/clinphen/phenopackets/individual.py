from datetime import datetime
from operator import not_
from typing import Literal

from pydantic import Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none

from .._fields import FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .time_element import TimeElement
from .vital_status import VitalStatus


class Individual(BentoClinPhenModel):
    id: str
    alternate_ids: list[str] = Field(default_factory=list, exclude_if=not_)  # TODO: format
    date_of_birth: datetime | None = FIELD_NULLABLE
    time_at_last_encounter: TimeElement | None = FIELD_NULLABLE
    vital_status: VitalStatus | None = FIELD_NULLABLE
    sex: Literal["UNKNOWN_SEX", "FEMALE", "MALE", "OTHER_SEX"] | None = FIELD_NULLABLE  # TODO: default to unknown sex?
    karyotypic_sex: Literal[
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
    ] | None = FIELD_NULLABLE  # TODO: default to unknown karyotype?
    gender: OntologyClass | None = Field(default=None, exclude_if=is_none)
    taxonomy: OntologyClass | None = Field(default=None, exclude_if=is_none)
