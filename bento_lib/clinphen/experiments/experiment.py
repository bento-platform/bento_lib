from typing import Literal

from pydantic import AnyUrl, BaseModel

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .experiment_result import ExperimentResult
from .instrument import Instrument

__all__ = ["Experiment"]

type ExperimentType = Literal[
    # Genomics
    "WGS",
    "WES",
    "Genotyping",
    "Viral WGS",
    "DNA metabarcoding",
    # Transcriptomics
    "mRNA-Seq",
    "RNA-Seq",
    "smRNA-Seq",
    "miRNA-Seq",
    "scRNA-Seq",
    "snRNA-Seq",
    # Epigenomics
    "DNA Methylation",
    "WGBS",
    "ChIP-Seq",
    "CUT&RUN",
    "CUT&Tag",
    "ATAC-Seq",
    "scATAC-Seq",
    # 3D Genomics
    "Hi-C",
    "scHi-C",
    # Multi-Omics
    "Multiome",
    # Other omics
    "Proteomic profiling",
    "Neutralizing antibody titers",
    "Metabolite profiling",
    "Antibody measurement",
    "Other",
]
type StudyType = Literal[
    "Genomics",
    "Epigenomics",
    "Metagenomics",
    "Transcriptomics",
    "Serology",
    "Metabolomics",
    "Proteomics",
    "3D Genomics",
    "Multi-Omics",
    "Other",
]
type Molecule = Literal[
    "total RNA",
    "polyA RNA",
    "cytoplasmic RNA",
    "nuclear RNA",
    "small RNA",
    "genomic DNA",
    "protein",
    "chromatin",
    "Other",
]
type LibraryStrategy = Literal[
    "WGS",
    "WES",
    "RNA-Seq",
    "Bisulfite-Seq",
    "ChIP-Seq",
    "ATAC-Seq",
    "Hi-C",
    "RAD-Seq",
    "ddRAD-Seq",
    "GT-Seq",
    "AMPLICON",
    "GBS",
    "Other",
]
type LibrarySource = Literal[
    "Genomic",
    "Genomic Single Cell",
    "Transcriptomic",
    "Transcriptomic Single Cell",
    "Metagenomic",
    "Metatranscriptomic",
    "Environmental DNA",
    "Environmental RNA",
    "Synthetic",
    "Viral RNA",
    "Other",
]
type LibrarySelection = Literal[
    "Random", "PCR", "Random PCR", "RT-PCR", "MF", "Exome capture", "ChIP", "PolyA", "Restriction Digest", "Other"
]
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
    insert_size: int | None = FIELD_NULLABLE
    protocol_url: AnyUrl | None = FIELD_NULLABLE
    extraction_protocol: str = FIELD_BLANKABLE
    reference_registry_id: str = FIELD_BLANKABLE
    qc_flags: list[str] = FIELD_LIST_OR_EMPTY
    extra_properties: dict  # TODO
    # other entities
    biosample: str  # ID of biosample
    instrument: Instrument | None = FIELD_NULLABLE
    experiment_results: list[ExperimentResult]
