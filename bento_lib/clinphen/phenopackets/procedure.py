from pydantic import BaseModel

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_NULLABLE
from .time_element import TimeElement

__all__ = ["Procedure"]


class Procedure(BaseModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/procedure.html
    """
    code: OntologyClass
    body_site: OntologyClass | None = FIELD_NULLABLE
    performed: TimeElement | None = FIELD_NULLABLE
