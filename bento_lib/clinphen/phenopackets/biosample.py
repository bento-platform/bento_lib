from pydantic import Field

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .._models import BentoClinPhenExtraPropsModel
from ..geo.geo_location import GeoLocation
from .file import File
from .measurement import Measurement
from .phenotypic_feature import PhenotypicFeature
from .procedure import Procedure
from .time_element import TimeElement

__all__ = ["Biosample"]


class Biosample(BentoClinPhenExtraPropsModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/biosample.html
    """

    # canonical fields from Phenopackets V2
    id: str = Field(..., min_length=1)
    individual_id: str | None = FIELD_NULLABLE
    derived_from_id: str | None = FIELD_NULLABLE
    description: str = FIELD_BLANKABLE
    sampled_tissue: OntologyClass | None = FIELD_NULLABLE
    sample_type: OntologyClass | None = FIELD_NULLABLE
    phenotypic_features: list[PhenotypicFeature] = FIELD_LIST_OR_EMPTY
    measurements: list[Measurement] = FIELD_LIST_OR_EMPTY
    taxonomy: OntologyClass | None = FIELD_NULLABLE
    time_of_collection: TimeElement | None = FIELD_NULLABLE
    histological_diagnosis: OntologyClass | None = FIELD_NULLABLE
    tumor_progression: OntologyClass | None = FIELD_NULLABLE
    tumor_grade: OntologyClass | None = FIELD_NULLABLE
    pathological_stage: OntologyClass | None = FIELD_NULLABLE
    pathological_tnm_finding: list[OntologyClass] = FIELD_LIST_OR_EMPTY
    diagnostic_markers: list[OntologyClass] = FIELD_LIST_OR_EMPTY
    procedure: Procedure | None = FIELD_NULLABLE
    files: list[File] = FIELD_LIST_OR_EMPTY
    material_sample: OntologyClass | None = FIELD_NULLABLE
    sample_processing: OntologyClass | None = FIELD_NULLABLE
    sample_storage: OntologyClass | None = FIELD_NULLABLE

    # Bento extended field
    location_collected: GeoLocation | None = FIELD_NULLABLE
