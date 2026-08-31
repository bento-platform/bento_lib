from pydantic import Field

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .evidence import Evidence
from .time_element import TimeElement

__all__ = ["PhenotypicFeature"]


class PhenotypicFeature(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/phenotype.html
    """
    description: str = FIELD_BLANKABLE
    type: OntologyClass
    excluded: bool = Field(default=False)
    severity: OntologyClass | None = FIELD_NULLABLE
    modifiers: list[OntologyClass] = FIELD_LIST_OR_EMPTY
    onset: TimeElement | None = FIELD_NULLABLE
    resolution: TimeElement | None = FIELD_NULLABLE
    evidence: list[Evidence] = FIELD_LIST_OR_EMPTY
