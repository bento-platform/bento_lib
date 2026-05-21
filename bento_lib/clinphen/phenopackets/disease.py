from operator import not_
from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none
from .time_element import TimeElement

__all__ = ["Disease"]


class Disease(BaseModel):
    term: OntologyClass
    excluded: bool | None = Field(default=None, exclude_if=is_none)
    onset: TimeElement | None = Field(default=None, exclude_if=is_none)
    resolution: TimeElement | None = Field(default=None, exclude_if=is_none)
    disease_stage: list[OntologyClass] = Field(default_factory=list, alias="diseaseStage", exclude_if=not_)
    clinical_tnm_finding: list[OntologyClass] = Field(default_factory=list, alias="clinicalTnmFinding", exclude_if=not_)
    primary_site: OntologyClass | None = Field(default=None, alias="primarySite", exclude_if=is_none)
    laterality: OntologyClass | None = Field(default=None, exclude_if=is_none)
