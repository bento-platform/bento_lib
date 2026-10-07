from typing import Literal

from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none

from .._fields import FIELD_NULLABLE
from .time_element import TimeElement

__all__ = ["VitalStatus"]


class VitalStatus(BaseModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/vital-status.html
    """

    status: Literal["UNKNOWN_STATUS", "ALIVE", "DECEASED"]
    time_of_death: TimeElement | None = FIELD_NULLABLE
    cause_of_death: OntologyClass | None = FIELD_NULLABLE
    survival_time_in_days: int | None = Field(default=None, exclude_if=is_none, ge=0)

    # TODO: additional validation
