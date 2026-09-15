from pydantic import Field

from bento_lib.ontologies.models import OntologyClass

from .._fields import field_list_or_empty, field_nullable
from .._models import BentoClinPhenModel
from .time_element import TimeElement

__all__ = ["Disease"]


class Disease(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/disease.html
    """

    term: OntologyClass = Field(..., description="Ontology class representing the disease.")
    excluded: bool | None = field_nullable(
        description="Whether the disease was observed or not. Negates the disease if true."
    )
    onset: TimeElement | None = field_nullable(description="The age or time of onset of the disease.")
    resolution: TimeElement | None = field_nullable(
        description="The age or time of resolution of (abatement/recovery from) the disease."
    )
    disease_stage: list[OntologyClass] = field_list_or_empty(
        description="List of ontology classes representing the disease stage."
    )
    clinical_tnm_finding: list[OntologyClass] = field_list_or_empty(
        description="List of ontology classes representing the tumour TNM score, if describing cancer."
    )
    primary_site: OntologyClass | None = field_nullable(description="The primary site of the disease.")
    laterality: OntologyClass | None = field_nullable(
        description="Laterality (left/right) of the diagnosis, if applicable."
    )
