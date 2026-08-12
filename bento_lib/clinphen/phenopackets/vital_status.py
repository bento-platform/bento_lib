from pydantic import BaseModel, Field
from typing import Literal

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none
from .time_element import TimeElement

__all__ = ["VitalStatus"]


class VitalStatus(BaseModel):
    status: Literal["UNKNOWN_STATUS", "ALIVE", "DECEASED"]
    time_of_death: TimeElement | None = Field(default=None, exclude_if=is_none)
    cause_of_death: OntologyClass | None = Field(default=None, exclude_if=is_none)
    survival_time_in_days: int | None = Field(default=None, exclude_if=is_none, ge=0)

    # TODO: additional validation
