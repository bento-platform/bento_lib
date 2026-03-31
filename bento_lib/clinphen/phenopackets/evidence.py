from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none

from .external_reference import ExternalReference

__all__ = ["Evidence"]


class Evidence(BaseModel):
    evidence_code: OntologyClass
    reference: ExternalReference | None = Field(default=None, exclude_if=is_none)
