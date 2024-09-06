from pydantic import BaseModel, Field, HttpUrl
from typing import Annotated

from .types import PhenoV2Resource, PhenoV2OntologyClassDict

NC_NAME_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9.\-_]*$"
CURIE_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9.\-_]*:[a-zA-Z0-9.\-_]+$"


class OntologyResource(BaseModel):
    """
    Inspired by the Phenopackets v2 Resource model:
    https://phenopacket-schema.readthedocs.io/en/latest/resource.html
    """

    # From Phenopackets v2: "For OBO ontologies, the value of this string MUST always be the official OBO ID, which is
    #   always equivalent to the ID prefix in lower case. Examples: hp, go, mp, mondo Consult http://obofoundry.org for
    #   a complete list. For other resources which do not use native CURIE identifiers (e.g. SNOMED, UniProt, ClinVar),
    #   use the prefix in identifiers.org."
    id: str

    # From Phenopackets v2: "The name of the ontology referred to by the id element, for example, The Human Phenotype
    #   Ontology. For OBO Ontologies, the value of this string SHOULD be the same as the title field on
    #   http://obofoundry.org. Other resources should use the official title for that resource. Note that this field is
    #   purely for information purposes and software should not encode any assumptions."
    name: str
    url: HttpUrl
    # From Phenopackets v2: "The prefix used in the CURIE of an OntologyClass e.g. HP, MP, ECO for example an HPO term
    #   will have a CURIE like this - HP:0012828 which should be used in combination with the iri_prefix to form a
    #   fully-resolvable IRI."
    # Since we use it in a CURIE prefix context, it must match a valid NCName:
    # https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-NCName
    namespace_prefix: Annotated[str, Field(pattern=NC_NAME_PATTERN)]
    iri_prefix: HttpUrl

    def make_term(self, id_: str, label: str) -> "OntologyTerm":
        return OntologyTerm(ontology=self, id=id_, label=label)


class VersionedOntologyResource(OntologyResource):
    version: str

    def to_phenopackets_repr(self) -> PhenoV2Resource:
        return self.model_dump(mode="json", include={"id", "version", "name", "url", "namespace_prefix", "iri_prefix"})


class OntologyTerm(BaseModel):
    """
    Inspired by the Phenopackets v2 OntologyClass model:
    https://phenopacket-schema.readthedocs.io/en/latest/ontologyclass.html
    """

    ontology: VersionedOntologyResource
    id: Annotated[str, Field(pattern=CURIE_PATTERN)]
    label: str

    def to_phenopackets_repr(self) -> PhenoV2OntologyClassDict:
        return self.model_dump(mode="json", include={"id", "label"})
