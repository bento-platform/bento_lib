from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .time_element import TimeElement

__all__ = ["Disease"]


class Disease(BentoClinPhenModel):
    term: OntologyClass
    excluded: bool | None = FIELD_NULLABLE
    onset: TimeElement | None = FIELD_NULLABLE
    resolution: TimeElement | None = FIELD_NULLABLE
    disease_stage: list[OntologyClass] = FIELD_LIST_OR_EMPTY
    clinical_tnm_finding: list[OntologyClass] = FIELD_LIST_OR_EMPTY
    primary_site: OntologyClass | None = FIELD_NULLABLE
    laterality: OntologyClass | None = FIELD_NULLABLE
