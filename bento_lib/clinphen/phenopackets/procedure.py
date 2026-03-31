from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none
from .time_element import TimeElement

__all__ = ["Procedure"]


class Procedure(BaseModel):
    code: OntologyClass
    body_site: OntologyClass | None = Field(default=None, exclude_if=is_none)
    performed: TimeElement | None = Field(default=None, exclude_if=is_none)
