from typing import Literal

from pydantic import Field

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY, FIELD_NULLABLE
from .._models import BentoClinPhenModel

__all__ = [
    # phenopacket enums / literals
    "ProgressStatus",
    "InterpretationStatus",
    "AcmgPathogenicityClassification",
    "TherapeuticActionability",
    # pydantic models
    "GeneDescriptor",
    "VcfRecord",
    "VariationDescriptor",
    "VariantInterpretation",
    "GenomicInterpretation",
    "Diagnosis",
    "Interpretation",
]


type ProgressStatus = Literal["UNKNOWN_PROGRESS", "IN_PROGRESS", "COMPLETED", "SOLVED", "UNSOLVED"]

type InterpretationStatus = Literal["UNKNOWN_STATUS", "REJECTED", "CANDIDATE", "CONTRIBUTORY", "CAUSATIVE"]

type AcmgPathogenicityClassification = Literal[
    "NOT_PROVIDED", "BENIGN", "LIKELY_BENIGN", "UNCERTAIN_SIGNIFICANCE", "LIKELY_PATHOGENIC", "PATHOGENIC"
]

type TherapeuticActionability = Literal["UNKNOWN_ACTIONABILITY", "NOT_ACTIONABLE", "ACTIONABLE"]

type MoleculeContext = Literal["unspecified_molecule_context", "genomic", "transcript", "protein"]


class GeneDescriptor(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/gene.html
    """

    value_id: str
    symbol: str
    description: str = FIELD_BLANKABLE
    alternate_ids: list[str] = FIELD_LIST_OR_EMPTY
    xrefs: list[str] = FIELD_LIST_OR_EMPTY
    alternate_symbols: list[str] = FIELD_LIST_OR_EMPTY


class VcfRecord(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/variant.html#vcfrecord
    """

    genome_assembly: str
    chrom: str
    pos: int
    id: str = FIELD_BLANKABLE
    ref: str = Field(..., min_length=1)
    alt: str
    qual: str = FIELD_BLANKABLE
    filter: str = FIELD_BLANKABLE
    info: str = FIELD_BLANKABLE


class Expression(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/variant.html#expression
    """

    syntax: str
    value: str
    version: str | None = FIELD_NULLABLE


class Extension(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/variant.html#extension
    """

    name: str
    value: str


class VariationDescriptor(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/variant.html
    """

    id: str = Field(..., min_length=1)
    variation: dict | None = FIELD_NULLABLE  # TODO: VRS variation model
    label: str = FIELD_BLANKABLE
    description: str = FIELD_BLANKABLE
    gene_context: GeneDescriptor | None = FIELD_NULLABLE
    expressions: list[Expression] = FIELD_LIST_OR_EMPTY
    vcf_record: VcfRecord | None = FIELD_NULLABLE
    xrefs: list[str] = FIELD_LIST_OR_EMPTY
    alternate_labels: list[str] = FIELD_LIST_OR_EMPTY
    extensions: list[Extension] = FIELD_LIST_OR_EMPTY
    molecule_context: MoleculeContext
    structural_type: OntologyClass | None = FIELD_NULLABLE
    vrs_ref_allele_seq: str = FIELD_BLANKABLE
    allelic_state: OntologyClass | None = FIELD_NULLABLE


class VariantInterpretation(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/variant-interpretation.html
    """

    acmg_pathogenicity_classification: AcmgPathogenicityClassification
    therapeutic_actionability: TherapeuticActionability
    variation_descriptor: VariationDescriptor


class GenomicInterpretation(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/genomic-interpretation.html
    """

    subject_or_biosample_id: str = Field(..., min_length=1)
    interpretation_status: InterpretationStatus
    call: GeneDescriptor | VariantInterpretation


class Diagnosis(BentoClinPhenModel):
    disease: OntologyClass
    genomic_interpretations: list[GenomicInterpretation] = FIELD_LIST_OR_EMPTY


class Interpretation(BentoClinPhenModel):
    id: str
    progress_status: ProgressStatus
    diagnosis: Diagnosis | None = FIELD_NULLABLE
    summary: str = FIELD_BLANKABLE
