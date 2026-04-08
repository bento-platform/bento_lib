from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import eq_blank

__all__ = ["PhenotypicFeature"]


class PhenotypicFeature(BaseModel):
    description: str = Field(default="", exclude_if=eq_blank)
    type: OntologyClass
    excluded: bool = Field(default=False)
