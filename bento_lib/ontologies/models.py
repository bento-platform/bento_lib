from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, model_validator

from .types import PhenoV2Resource, PhenoV2OntologyClassDict

__all__ = [
    "NC_NAME_PATTERN",
    "CURIE_PATTERN",
    "OntologyResource",
    "VersionedOntologyResource",
    "OntologyClass",
    "ResourceOntologyClass",
]

NC_NAME_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9.\-_]*$"
CURIE_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9.\-_]*:[a-zA-Z0-9.\-_]+$"


class OntologyResource(BaseModel):
    """
    Model for an ontology resource, including a link to a machine-readable ontology definition file.
    Inspired by the Phenopackets v2 Resource model:
    https://phenopacket-schema.readthedocs.io/en/latest/resource.html
    """

    # From Phenopackets v2: "For OBO ontologies, the value of this string MUST always be the official OBO ID, which is
    #   always equivalent to the ID prefix in lower case. Examples: hp, go, mp, mondo Consult http://obofoundry.org for
    #   a complete list. For other resources which do not use native CURIE identifiers (e.g. SNOMED, UniProt, ClinVar),
    #   use the prefix in identifiers.org."
    id: str = Field(
        ...,
        title="ID",
        description="Ontology ID. For OBO ontologies, this must be the official OBO ID for Phenopackets compatibility.",
        min_length=1,
    )

    # From Phenopackets v2: "The name of the ontology referred to by the id element, for example, The Human Phenotype
    #   Ontology. For OBO Ontologies, the value of this string SHOULD be the same as the title field on
    #   http://obofoundry.org. Other resources should use the official title for that resource. Note that this field is
    #   purely for information purposes and software should not encode any assumptions."
    name: str = Field(..., title="Name", description="Ontology name, e.g., The Human Phenotype Ontology", min_length=1)
    url: HttpUrl = Field(..., title="URL", description="URL to the machine-readable ontology definition file")
    # From Phenopackets v2: "The prefix used in the CURIE of an OntologyClass e.g. HP, MP, ECO for example an HPO class
    #   will have a CURIE like this - HP:0012828 which should be used in combination with the iri_prefix to form a
    #   fully-resolvable IRI."
    # Since we use it in a CURIE prefix context, it must match a valid NCName:
    # https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-NCName
    namespace_prefix: str = Field(
        ...,
        title="Namespace prefix",
        description="Prefix used in the CURIE of an ontology class",
        pattern=NC_NAME_PATTERN,
    )
    iri_prefix: HttpUrl = Field(
        ...,
        title="IRI prefix",
        description="URL prefix used in combination with part of a CURIE to fully resolve an ontology class",
    )

    repository_url: HttpUrl | None = Field(
        default=None, title="Repository URL", description="Development repository URL, useful for tracking new versions"
    )

    def make_class(self, id_: str, label: str) -> ResourceOntologyClass:
        return ResourceOntologyClass(ontology=self, id=id_, label=label)

    def as_versioned(self, url: str, version: str) -> VersionedOntologyResource:
        return VersionedOntologyResource(
            **self.model_dump(include={"id", "name", "namespace_prefix", "iri_prefix"}),
            url=HttpUrl(url),
            version=version,
        )


class VersionedOntologyResource(OntologyResource):
    """
    A specific version of an ontology resource, and ideally a URL which points to the specific version of the
    machine-readable ontology definition file.
    """

    version: str = Field(..., title="Version", description="Ontology resource version")

    def to_phenopackets_repr(self) -> PhenoV2Resource:
        return self.model_dump(mode="json", include={"id", "version", "name", "url", "namespace_prefix", "iri_prefix"})


class OntologyClass(BaseModel):
    """
    Model for an ontology class, with a CURIE ID and a label. Inspired by the Phenopackets v2 OntologyClass model:
    https://phenopacket-schema.readthedocs.io/en/latest/ontologyclass.html
    """

    id: str = Field(..., pattern=CURIE_PATTERN, title="ID", description="CURIE-formatted ontology class ID")
    label: str = Field(..., title="Label", description="Human-readable label for the ontology class")

    def to_phenopackets_repr(self) -> PhenoV2OntologyClassDict:
        return self.model_dump(mode="json", include={"id", "label"})


class ResourceOntologyClass(OntologyClass):
    """
    Ontology class with a back-reference to a descriptor for the versioned ontology resource the class is from.
    """

    ontology: OntologyResource = Field(
        ...,
        title="Ontology resource",
        description="Ontology resource where the class comes from (either versioned or unversioned).",
    )

    @model_validator(mode="after")
    def check_curie(self) -> "ResourceOntologyClass":
        if not self.id.startswith(self.ontology.namespace_prefix + ":"):
            raise ValueError("class CURIE must start with ontology resource namespace prefix")
        return self
