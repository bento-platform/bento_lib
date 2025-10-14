from pydantic import HttpUrl
from .models import OntologyResource

__all__ = [
    # EFO
    "EFO",
    "EFO_3_81_0",
    # MONDO
    "MONDO",
    "MONDO_2025_04_01",
    # NCBITaxon
    "NCBI_TAXON",
    "NCBI_TAXON_2025_03_13",
    # NCIT
    "NCIT",
    "NCIT_2024_05_07",
    # OBI
    "OBI",
    "OBI_2025_03_06",
    # SO
    "SO",
    # UBERON
    "UBERON",
]


# === EFO ==============================================================================================================

EFO = OntologyResource(
    id="efo",
    name="Experimental Factor Ontology",
    namespace_prefix="EFO",
    iri_prefix=HttpUrl("http://www.ebi.ac.uk/efo/EFO_"),
    url=HttpUrl("http://www.ebi.ac.uk/efo/efo.owl"),
    repository_url=HttpUrl("https://github.com/EBISPOT/efo"),
)
EFO_3_81_0 = EFO.as_versioned("https://www.ebi.ac.uk/efo/releases/v3.81.0/efo.owl", version="3.81.0")

# === MONDO ============================================================================================================

MONDO = OntologyResource(
    id="mondo",
    name="Mondo Disease Ontology",
    namespace_prefix="MONDO",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/MONDO_"),
    url=HttpUrl("http://purl.obolibrary.org/obo/mondo.owl"),
    repository_url=HttpUrl("https://github.com/monarch-initiative/mondo"),
)
MONDO_2025_04_01 = MONDO.as_versioned(
    url="https://purl.obolibrary.org/obo/mondo/releases/2025-09-02/mondo.owl",
    version="2025-09-02",
)

# === NCBITaxon ========================================================================================================

NCBI_TAXON = OntologyResource(
    id="ncbitaxon",
    name="NCBI organismal classification",
    namespace_prefix="NCBITaxon",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/NCBITaxon_"),
    url=HttpUrl("http://purl.obolibrary.org/obo/ncbitaxon.owl"),
    repository_url=HttpUrl("https://github.com/obophenotype/ncbitaxon"),
)
NCBI_TAXON_2025_03_13 = NCBI_TAXON.as_versioned(
    url="https://purl.obolibrary.org/obo/ncbitaxon/2025-03-13/ncbitaxon.owl",
    version="2025-03-13",
)

# === NCIT =============================================================================================================

NCIT = OntologyResource(
    id="ncit",
    name="NCI Thesaurus OBO Edition",
    namespace_prefix="NCIT",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/NCIT_"),
    url=HttpUrl("http://purl.obolibrary.org/obo/ncit.owl"),
    repository_url=HttpUrl("https://github.com/NCI-Thesaurus/thesaurus-obo-edition"),
)
NCIT_2024_05_07 = NCIT.as_versioned(
    url="https://purl.obolibrary.org/obo/ncit/releases/2024-05-07/ncit.owl",
    version="2024-05-07",
)

# === OBI ==============================================================================================================

OBI = OntologyResource(
    id="obi",
    name="Ontology for Biomedical Investigations",
    namespace_prefix="OBI",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/OBI_"),
    url=HttpUrl("https://purl.obolibrary.org/obo/obi.owl"),
    repository_url=HttpUrl("https://github.com/obi-ontology/obi"),
)
OBI_2025_03_06 = OBI.as_versioned(url="https://purl.obolibrary.org/obo/obi/2025-07-28/obi.owl", version="2025-07-28")

# === SO ===============================================================================================================

SO = OntologyResource(
    id="so",
    name="Sequence types and features ontology",
    namespace_prefix="SO",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/SO_"),
    url=HttpUrl("http://purl.obolibrary.org/obo/so.owl"),
    repository_url=HttpUrl("https://github.com/The-Sequence-Ontology/SO-Ontologies"),
)

# === UBERON ===========================================================================================================

UBERON = OntologyResource(
    id="uberon",
    name="Uberon multi-species anatomy ontology",
    namespace_prefix="UBERON",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/UBERON_"),
    url=HttpUrl("http://purl.obolibrary.org/obo/uberon.owl"),
)
