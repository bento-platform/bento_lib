from .models import OntologyResource, VersionedOntologyResource

__all__ = [
    # EFO
    "EFO",
    "EFO_3_69_0",
    # MONDO
    "MONDO",
    "MONDO_2024_09_03",
    # NCBITaxon
    "NCBI_TAXON",
    "NCBI_TAXON_2024_07_03",
    # NCIT
    "NCIT",
    "NCIT_2024_05_07",
    # OBI
    "OBI",
    "OBI_2024_06_10",
    # SO
    "SO",
    # UBERON
    "UBERON",
]


def _versioned(ont: OntologyResource, url: str, version: str) -> VersionedOntologyResource:
    return VersionedOntologyResource(
        **ont.model_dump(include={"id", "name", "namespace_prefix", "iri_prefix"}),
        url=url,
        version=version,
    )


# === EFO ==============================================================================================================

EFO = OntologyResource(
    id="efo",
    name="Experimental Factor Ontology",
    namespace_prefix="EFO",
    iri_prefix="http://www.ebi.ac.uk/efo/EFO_",
    url="http://www.ebi.ac.uk/efo/efo.owl",
)
EFO_3_69_0 = _versioned(EFO, "http://www.ebi.ac.uk/efo/releases/v3.69.0/efo.owl", version="3.69.0")

# === MONDO ============================================================================================================

MONDO = OntologyResource(
    id="mondo",
    name="Mondo Disease Ontology",
    namespace_prefix="MONDO",
    iri_prefix="http://purl.obolibrary.org/obo/MONDO_",
    url="http://purl.obolibrary.org/obo/mondo.owl",
)
MONDO_2024_09_03 = _versioned(
    MONDO,
    url="http://purl.obolibrary.org/obo/mondo/releases/2024-09-03/mondo.owl",
    version="2024-09-03",
)

# === NCBITaxon ========================================================================================================

NCBI_TAXON = OntologyResource(
    id="ncbitaxon",
    name="NCBI organismal classification",
    namespace_prefix="NCBITaxon",
    iri_prefix="http://purl.obolibrary.org/obo/NCBITaxon_",
    url="http://purl.obolibrary.org/obo/ncbitaxon.owl",
)
NCBI_TAXON_2024_07_03 = _versioned(
    NCBI_TAXON,
    url="http://purl.obolibrary.org/obo/ncbitaxon/2024-07-03/ncbitaxon.owl",
    version="2024-07-03",
)

# === NCIT =============================================================================================================

NCIT = OntologyResource(
    id="ncit",
    name="NCI Thesaurus OBO Edition",
    namespace_prefix="NCIT",
    iri_prefix="http://purl.obolibrary.org/obo/NCIT_",
    url="http://purl.obolibrary.org/obo/ncit.owl",
)
NCIT_2024_05_07 = _versioned(
    NCIT,
    url="http://purl.obolibrary.org/obo/ncit/releases/2024-05-07/ncit.owl",
    version="2024-05-07",
)

# === OBI ==============================================================================================================

OBI = OntologyResource(
    id="obi",
    name="Ontology for Biomedical Investigations",
    namespace_prefix="OBI",
    iri_prefix="http://purl.obolibrary.org/obo/OBI_",
    url="http://purl.obolibrary.org/obo/obi.owl",
)
OBI_2024_06_10 = _versioned(OBI, url="http://purl.obolibrary.org/obo/obi/2024-06-10/obi.owl", version="2024-06-10")

# === SO ===============================================================================================================

SO = OntologyResource(
    id="so",
    name="Sequence types and features ontology",
    namespace_prefix="SO",
    iri_prefix="http://purl.obolibrary.org/obo/SO_",
    url="http://purl.obolibrary.org/obo/so.owl",
)
SO_2024_06_05 = _versioned(SO, url="http://purl.obolibrary.org/obo/so/2024-06-05/so.owl", version="2024-06-05")

# === UBERON ===========================================================================================================

UBERON = OntologyResource(
    id="uberon",
    name="Uberon multi-species anatomy ontology",
    namespace_prefix="UBERON",
    iri_prefix="http://purl.obolibrary.org/obo/UBERON_",
    url="http://purl.obolibrary.org/obo/uberon.owl",
)
