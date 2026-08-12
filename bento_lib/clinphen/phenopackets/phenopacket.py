from operator import not_
from pydantic import BaseModel, Field

from bento_lib.utils.operators import is_none
from .biosample import Biosample
from .disease import Disease
from .file import File
from .individual import Individual
from .interpretation import Interpretation
from .measurement import Measurement
from .meta_data import MetaData
from .phenotypic_feature import PhenotypicFeature


class Phenopacket(BaseModel):
    id: str
    subject: Individual | None = Field(default=None, exclude_if=is_none)
    phenotypic_features: list[PhenotypicFeature] = Field(default_factory=list, exclude_if=not_)
    measurements: list[Measurement] = Field(default_factory=list, exclude_if=not_)
    biosamples: list[Biosample] = Field(default_factory=list, exclude_if=not_)
    interpretations: list[Interpretation] = Field(default_factory=list, exclude_if=not_)
    diseases: list[Disease] = Field(default_factory=list, exclude_if=not_)
    medical_actions: list[MedicalAction] = Field(default_factory=list, exclude_if=not_)
    files: list[File] = Field(default_factory=list, exclude_if=not_)
    meta_data: MetaData
