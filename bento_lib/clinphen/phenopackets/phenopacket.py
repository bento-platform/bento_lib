from .._fields import FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .biosample import Biosample
from .disease import Disease
from .file import File
from .individual import Individual
from .interpretation import Interpretation
from .measurement import Measurement
from .medical_actions import MedicalAction
from .meta_data import MetaData
from .phenotypic_feature import PhenotypicFeature

__all__ = ["Phenopacket"]


class Phenopacket(BentoClinPhenModel):
    id: str
    subject: Individual | None = FIELD_NULLABLE
    phenotypic_features: list[PhenotypicFeature] = FIELD_LIST_OR_EMPTY
    measurements: list[Measurement] = FIELD_LIST_OR_EMPTY
    biosamples: list[Biosample] = FIELD_LIST_OR_EMPTY
    interpretations: list[Interpretation] = FIELD_LIST_OR_EMPTY
    diseases: list[Disease] = FIELD_LIST_OR_EMPTY
    medical_actions: list[MedicalAction] = FIELD_LIST_OR_EMPTY
    files: list[File] = FIELD_LIST_OR_EMPTY
    meta_data: MetaData
