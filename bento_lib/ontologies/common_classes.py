from .common_resources import NCBI_TAXON, OBI, SO, UBERON

__all__ = [
    # NCBITaxon
    "NCBI_TAXON_HOMO_SAPIENS",
    "NCBI_TAXON_MUS_MUSCULUS",
    "NCBI_TAXON_URSUS_MARITIMUS",
    # OBI
    #  - Assays
    "OBI_16S_RRNA_ASSAY",
    "OBI_EXOME_SEQUENCING_ASSAY",
    "OBI_METABOLITE_PROFILING_ASSAY",
    "OBI_PROTEOMIC_PROFILING_BY_ARRAY_ASSAY",
    "OBI_RNA_SEQ_ASSAY",
    "OBI_WHOLE_GENOME_SEQUENCING_ASSAY",
    #  - Specimens
    "OBI_BLOOD_SPECIMEN",
    "OBI_FECES_SPECIMEN",
    "OBI_MILK_SPECIMEN",
    "OBI_NASAL_SWAB_SPECIMEN",
    "OBI_SPUTUM_SPECIMEN",
    # SO
    "SO_GENOMIC_DNA",
    # UBERON
    "UBERON_BLOOD",
    "UBERON_FECES",
    "UBERON_MILK",
    "UBERON_SPUTUM",
]


# === NCBITaxon ========================================================================================================

NCBI_TAXON_HOMO_SAPIENS = NCBI_TAXON.make_class("NCBITaxon:9606", "Homo sapiens")
NCBI_TAXON_MUS_MUSCULUS = NCBI_TAXON.make_class("NCBITaxon:10090", "Mus musculus")
NCBI_TAXON_URSUS_MARITIMUS = NCBI_TAXON.make_class("NCBITaxon:29073", "Ursus maritimus")

# === OBI ==============================================================================================================

#  - Assays

OBI_16S_RRNA_ASSAY = OBI.make_class("OBI:0002763", "16s ribosomal gene sequencing assay")
OBI_EXOME_SEQUENCING_ASSAY = OBI.make_class("OBI:0002118", "exome sequencing assay")
OBI_GENOTYPING_BY_SNP_ARRAY_ASSAY = OBI.make_class("OBI:0002031", "genotyping by SNP array assay")
OBI_METABOLITE_PROFILING_ASSAY = OBI.make_class("OBI:0000366", "metabolite profiling assay")
OBI_PROTEOMIC_PROFILING_BY_ARRAY_ASSAY = OBI.make_class("OBI:0001318", "proteomic profiling by array assay")
OBI_RNA_SEQ_ASSAY = OBI.make_class("OBI:0001271", "RNA-seq assay")
OBI_WHOLE_GENOME_SEQUENCING_ASSAY = OBI.make_class("OBI:0002117", "whole genome sequencing assay")

#  - Specimens

OBI_BLOOD_SPECIMEN = OBI.make_class("OBI:0000655", "blood specimen")
OBI_FECES_SPECIMEN = OBI.make_class("OBI:0002503", "feces specimen")
OBI_MILK_SPECIMEN = OBI.make_class("OBI:0002505", "milk specimen")
OBI_NASAL_SWAB_SPECIMEN = OBI.make_class("OBI:0000917", "nasal swab specimen")
OBI_SPUTUM_SPECIMEN = OBI.make_class("OBI:0002508", "sputum specimen")

# === SO ===============================================================================================================

SO_GENOMIC_DNA = SO.make_class("SO:0000991", "genomic DNA")

# === UBERON ===========================================================================================================

UBERON_BLOOD = UBERON.make_class("UBERON:0000178", "blood")
UBERON_FECES = UBERON.make_class("UBERON:0001988", "feces")
UBERON_MILK = UBERON.make_class("UBERON:0001913", "milk")
UBERON_SPUTUM = UBERON.make_class("UBERON:0007311", "sputum")
