from datetime import datetime
from operator import not_
from pydantic import BaseModel, Field
from typing import Literal

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none
from .time_element import TimeElement
from .vital_status import VitalStatus


class Individual(BaseModel):
    id: str
    alternate_ids: list[str] = Field(default_factory=list, alias="alternateIds", exclude_if=not_)  # TODO: format
    date_of_birth: datetime
    time_at_last_encounter: TimeElement | None = Field(default=None, alias="timeAtLastEncounter", exclude_if=is_none)
    vital_status: VitalStatus
    sex: Literal["UNKNOWN_SEX", "FEMALE", "MALE", "OTHER_SEX"] | None  # TODO: default to unknown sex?
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
    ]  # TODO: default to unknown karyotype?
    gender: OntologyClass | None = Field(default=None, exclude_if=is_none)
    taxonomy: OntologyClass | None = Field(default=None, exclude_if=is_none)
