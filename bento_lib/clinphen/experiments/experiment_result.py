from datetime import date
from pydantic import AnyUrl, BaseModel
from typing import Literal

__all__ = [
    "ExperimentResultIndex",
    "ExperimentResult",
]


class ExperimentResultIndex(BaseModel):
    url: AnyUrl
    # BAI:   http://samtools.github.io/hts-specs/SAMv1.pdf "BAI" )
    # BGZF:  BGZip index files (often .gzi)
    # CRAI:  https://samtools.github.io/hts-specs/CRAMv3.pdf "CRAM index"
    # CSI:   https://samtools.github.io/hts-specs/CSIv1.pdf
    # TABIX: https://samtools.github.io/hts-specs/tabix.pdf
    # TRIBBLE: GATK thing
    format: Literal["BAI", "BGZF", "CRAI", "CSI", "TABIX", "TRIBBLE"]


class ExperimentResult(BaseModel):
    # TODO: figure out ID mess
    description: str
    filename: str
    url: str
    indices: list[ExperimentResultIndex]
    genome_assembly_id: str
    # fmt: off
    file_format: Literal[
        "SAM", "BAM", "CRAM", "VCF", "BCF", "MAF", "GVCF", "BigWig", "BigBed", "FASTA", "FASTQ", "TAB", "SRA", "SRF",
        "SFF", "GFF", "PDF", "CSV", "TSV", "JPEG", "PNG", "GIF", "HTML", "MARKDOWN", "MP3", "M4A", "MP4", "DOCX", "XLS",
        "XLSX", "UNKNOWN", "OTHER"
    ] | None
    # fmt: on
    data_output_type: Literal["Raw data", "Derived data"] | None
    usage: str
    creation_date: date
    created_by: str
    extra_properties: dict  # TODO
