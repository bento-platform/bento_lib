from .common_resources import NCBI_TAXON, OBI, SO

__all__ = [
    # NCBITaxon
    "NCBI_TAXON_HOMO_SAPIENS",
    "NCBI_TAXON_MUS_MUSCULUS",
    # OBI
    "OBI_16S_RRNA_ASSAY",
    "OBI_RNA_SEQ_ASSAY",
    "OBI_PROTEOMIC_PROFILING_BY_ARRAY_ASSAY",
    "OBI_WHOLE_GENOME_SEQUENCING_ASSAY",
    # SO
    "SO_GENOMIC_DNA",
]


# === NCBITaxon ========================================================================================================

NCBI_TAXON_HOMO_SAPIENS = NCBI_TAXON.make_class("NCBITaxon:9606", "Homo sapiens")
NCBI_TAXON_MUS_MUSCULUS = NCBI_TAXON.make_class("NCBITaxon:10090", "Mus musculus")

# === OBI ==============================================================================================================

OBI_16S_RRNA_ASSAY = OBI.make_class("OBI:0002763", "16s ribosomal gene sequencing assay")
OBI_RNA_SEQ_ASSAY = OBI.make_class("OBI:0001271", "RNA-seq assay")
OBI_PROTEOMIC_PROFILING_BY_ARRAY_ASSAY = OBI.make_class("OBI:0001318", "proteomic profiling by array assay")
OBI_WHOLE_GENOME_SEQUENCING_ASSAY = OBI.make_class("OBI:0002117", "whole genome sequencing assay")

# === SO ===============================================================================================================

SO_GENOMIC_DNA = SO.make_class("SO:0000991", "genomic DNA")
