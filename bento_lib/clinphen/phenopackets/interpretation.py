from operator import not_
from pydantic import BaseModel, Field
from typing import Literal

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import eq_blank, is_none

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


class GeneDescriptor(BaseModel):
    value_id: str
    symbol: str
    description: str = Field(default="", exclude_if=eq_blank)
    alternate_ids: list[str] = Field(default_factory=list, exclude_if=not_)
    xrefs: list[str] = Field(default_factory=list, exclude_if=not_)
    alternate_symbols: list[str] = Field(default_factory=list, exclude_if=not_)


class VcfRecord(BaseModel):
    genome_assembly: str
    chrom: str
    pos: int
    id: str = Field(default="", exclude_if=eq_blank)
    ref: str
    alt: str
    qual: int | None = Field(default=None, exclude_if=is_none)
    filter: str = Field(default="", exclude_if=eq_blank)
    info: str = Field(default="", exclude_if=eq_blank)


class VariationDescriptor(BaseModel):
    id: str
    variation: Variation | None = Field(default=None, exclude_if=is_none)
    label: str = Field(default="", exclude_if=eq_blank)
    description: str = Field(default="", exclude_if=eq_blank)
    gene_context: GeneDescriptor | None = Field(default=None, exclude_if=is_none)
    expressions: list[Expression] = Field(default_factory=list, exclude_if=not_)
    vcf_record: VcfRecord | None = Field(default=None, exclude_if=is_none)
    xrefs: list[str] = Field(default_factory=list, exclude_if=not_)
    alternate_labels: list[str] = Field(default_factory=list, exclude_if=not_)
    extensions: list[Extension] = Field(default_factory=list, exclude_if=not_)
    molecule_context: MoleculeContext
    structural_type: OntologyClass | None = Field(default=None, exclude_if=is_none)
    vrs_ref_allele_seq: str = Field(default="", exclude_if=eq_blank)
    allelic_state: OntologyClass | None = Field(default=None, exclude_if=is_none)


class VariantInterpretation(BaseModel):
    acmg_pathogenicity_classification: AcmgPathogenicityClassification
    therapeutic_actionability: TherapeuticActionability
    variation_descriptor: VariationDescriptor


class GenomicInterpretation(BaseModel):
    subject_or_biosample_id: str
    interpretation_status: InterpretationStatus
    call: GeneDescriptor | VariantInterpretation


class Diagnosis(BaseModel):
    disease: OntologyClass
    genomic_interpretations: list[GenomicInterpretation] = Field(default_factory=list, exclude_if=not_)


class Interpretation(BaseModel):
    id: str
    progress_status: ProgressStatus
    diagnosis: Diagnosis | None = Field(default=None, exclude_if=is_none)
    summary: str = Field(default="", exclude_if=eq_blank)
