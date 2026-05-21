from pydantic import AnyUrl, BaseModel
from typing import Literal

from bento_lib.ontologies.models import OntologyClass
from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .experiment_result import ExperimentResult
from .instrument import Instrument

__all__ = ["Experiment"]

type ExperimentType = Literal[]  # TODO
type StudyType = Literal[]  # TODO
type Molecule = Literal[]  # TODO
type LibraryStrategy = Literal[]  # TODO
type LibrarySource = Literal[]  # TODO
type LibrarySelection = Literal[]  # TODO
type LibraryLayout = Literal["Single", "Paired"]


class Experiment(BaseModel):
    # required fields
    id: str
    experiment_type: ExperimentType
    # optional fields
    experiment_ontology: OntologyClass | None = FIELD_NULLABLE
    description: str = FIELD_BLANKABLE
    study_type: StudyType | None = FIELD_NULLABLE
    molecule: Molecule | None = FIELD_NULLABLE
    molecule_ontology: OntologyClass | None = FIELD_NULLABLE
    library_strategy: LibraryStrategy | None = FIELD_NULLABLE
    library_source: LibrarySource | None = FIELD_NULLABLE
    library_selection: LibrarySelection | None = FIELD_NULLABLE
    library_layout: LibraryLayout | None = FIELD_NULLABLE
    library_id: str = FIELD_BLANKABLE
    library_description: str = FIELD_BLANKABLE
    library_extract_id: str = FIELD_BLANKABLE
    insert_size: int | None
    protocol_url: AnyUrl
    extraction_protocol: str = FIELD_BLANKABLE
    reference_registry_id: str = FIELD_BLANKABLE
    qc_flags: list[str] = FIELD_LIST_OR_EMPTY
    extra_properties: dict  # TODO
    # other entities
    biosample: str  # ID of biosample
    instrument: Instrument | None = FIELD_NULLABLE
    experiment_results: list[ExperimentResult]
