__all__ = [
    "Role",
    "RoleAnnotated",
    "PublicationType",
    "PublicationVenueType",
    "Other",
    "Phone",
    "Contact",
    "Organization",
    "Person",
    "ParticipantCriteria",
    "Count",
    "License",
    "PublicationVenue",
    "Publication",
    "Logo",
    "SpatialCoverageProperties",
    "SpatialCoverageFeature",
    "Link",
    "TypedLink",
    "FundingSource",
    "LongDescription",
    "PersonOrOrganization",
    "DatasetModelBase",
    "DatasetModel",
    "ProjectScopedDatasetModel",
]

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from geojson_pydantic import Feature as GeoJSONFeature
from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)
from rdflib import BNode, Graph, URIRef
from rdflib import Literal as RdfLiteral
from rdflib.namespace import DCAT, DCTERMS, FOAF, RDF, SDO

from bento_lib.discovery import DiscoveryConfig
from bento_lib.i18n import EN, FR, TranslatableModel, TranslatedLiteral
from bento_lib.jsonld import JsonLd, ToRdf
from bento_lib.ontologies.models import OntologyClass, VersionedOntologyResource

Orcid = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")]

# Roles for individuals and organizations in a dataset
#  - includes terms that map to DataCite:
#      https://datacite-metadata-schema.readthedocs.io/en/4.6/appendices/appendix-1/contributorType/
#  - extends well beyond this to try to allow maximal descriptivity
# Turning formating off to preserve columnar structure
# fmt: off
Role = TranslatedLiteral(EN, FR)(
    # Leadership / oversight
    ("Principal Investigator",    "Chercheur principal"),
    ("Co-Investigator",           "Co-chercheur"),
    ("Sub-Investigator",          "Sous-chercheur"),
    ("Study Director",            "Directeur d'étude"),
    ("Project Lead",              "Chef de projet"),  # DataCite: ProjectLeader
    ("Project Manager",           "Gestionnaire de projet"),
    ("Contact Person",            "Personne-ressource"),  # DataCite: ContactPerson
    # Research team
    ("Researcher",                "Chercheur"),  # DataCite: Researcher
    ("Research Assistant",        "Assistant de recherche"),
    ("Data Scientist",            "Scientifique des données"),
    ("Statistician",              "Statisticien"),
    ("Study Coordinator",         "Coordonnateur d'étude"),
    ("Lab Technician",            "Technicien de laboratoire"),
    # Participants / human subjects
    ("Participant",               "Participant"),
    ("Subject",                   "Sujet"),
    ("Volunteer",                 "Volontaire"),
    # Other individual roles
    ("Editor",                    "Éditeur"),  # DataCite: Editor
    ("Translator",                "Traducteur"),  # DataCite: Translator
    # Organizational / institutional roles
    ("Principal Laboratory",      "Laboratoire principal"),
    ("Sponsoring Organization",   "Organisation commanditaire"),
    ("Collaborating Laboratory",  "Laboratoire collaborateur"),
    ("Collaborating Organization","Organisation collaboratrice"),
    ("Consortium",                "Consortium"),
    ("Distributor",               "Distributeur"),  # DataCite: Distributor
    ("Institution",               "Institution"),
    ("Hosting Institution",       "Institution hôte"),  # DataCite: HostingInstitution
    ("Site",                      "Site"),
    ("Research Center",           "Centre de recherche"),
    ("Research Group",            "Groupe de recherche"),  # DataCite: ResearchGroup
    ("Publisher",                 "Éditeur"),
    # Ethics & compliance
    ("IRB",                       "CÉR"),
    ("Ethics Board",              "Comité d'éthique"),
    ("Data Monitoring Committee", "Comité de surveillance des données"),
    ("Compliance Officer",        "Responsable de la conformité"),
    # Funding & support
    ("Sponsor",                   "Commanditaire"),  # DataCite: Sponsor
    ("Funder",                    "Bailleur de fonds"),
    ("Grant Agency",              "Organisme subventionnaire"),
    # Publications
    ("Author",                    "Auteur"),
    ("Corresponding Author",      "Auteur correspondant"),
    # Contributors (non-research)
    ("Consultant",                "Consultant"),
    ("Advisor",                   "Conseiller"),
    ("Reviewer",                  "Évaluateur"),
    # Data & technical roles
    ("Data Collector",            "Collecteur de données"),  # DataCite: DataCollector
    ("Data Provider",             "Fournisseur de données"),
    ("Data Controller",           "Responsable du traitement des données"),
    ("Data Processor",            "Sous-traitant des données"),
    ("Data Contributor",          "Contributeur de données"),
    ("Data Custodian",            "Gardien des données"),
    ("Data Manager",              "Gestionnaire de données"),  # DataCite: DataManager
    ("Data Producer",             "Producteur de données"),
    # External stakeholders
    ("Partner",                   "Partenaire"),
    ("Stakeholder",               "Partie prenante"),
    ("Community Representative",  "Représentant communautaire"),
    ("Other",                     "Autre"),
)
RoleAnnotated = Annotated[str, Role]

PublicationType = TranslatedLiteral(EN, FR)(
    # Articles and papers
    ("Journal Article",        "Article de revue"),
    ("Conference Paper",       "Article de conférence"),
    ("Workshop Paper",         "Article d'atelier"),
    ("Short Paper",            "Article court"),
    ("Poster",                 "Affiche"),
    ("Preprint",               "Prépublication"),
    # Books and long form
    ("Book",                   "Livre"),
    ("Book Chapter",           "Chapitre de livre"),
    ("Monograph",              "Monographie"),
    # Reports and gray literature
    ("Technical Report",       "Rapport technique"),
    ("White Paper",            "Livre blanc"),
    ("Working Paper",          "Document de travail"),
    # Academic qualifications
    ("Thesis",                 "Thèse"),
    ("Master's Thesis",        "Mémoire de maîtrise"),
    ("Doctoral Dissertation",  "Thèse de doctorat"),
    # Data and software
    ("Dataset",                "Jeu de données"),
    ("Software",               "Logiciel"),
    ("Software Paper",         "Article sur un logiciel"),
    # Multimedia
    ("Audio",                  "Audio"),
    ("Documentary",            "Documentaire"),
    ("Podcast",                "Balado"),
    ("Video",                  "Vidéo"),
    # Reviews and other
    ("Survey",                 "Enquête"),
    ("Review Article",         "Article de synthèse"),
    ("Editorial",              "Éditorial"),
    ("Commentary",             "Commentaire"),
    ("Patent",                 "Brevet"),
)
PublicationTypeAnnotated = Annotated[str, PublicationType]

PublicationVenueType = TranslatedLiteral(EN, FR)(
    ("Journal",             "Revue"),
    ("Conference",          "Conférence"),
    ("Workshop",            "Atelier"),
    ("Repository",          "Dépôt"),
    ("Publisher",           "Éditeur"),
    ("University",          "Université"),
    ("Data Repository",     "Dépôt de données"),
    ("Preprint Repository", "Dépôt de prépublications"),
)
PublicationVenueTypeAnnotated = Annotated[str, PublicationVenueType]

ParticipantCriterionType = TranslatedLiteral(EN, FR)(
    ("Inclusion", "Inclusion"),
    ("Exclusion", "Exclusion"),
    ("Other", "Autre"),
)
ParticipantCriterionTypeAnnotated = Annotated[str, ParticipantCriterionType]

LinkType = TranslatedLiteral(EN, FR)(
    ("Downloadable Artifact",  "Artéfact téléchargeable"),
    ("Data Management Plan",   "Plan de gestion des données"),
    ("Schema",                 "Schéma"),
    ("External Reference",     "Référence externe"),
    ("Data Access",            "Accès aux données"),
    ("Data Request Form",      "Formulaire de demande de données"),
)
LinkTypeAnnotated = Annotated[str, LinkType]
# fmt: on


class Other(BaseModel):
    """When a literal is not exhaustive"""

    other: str = Field(min_length=1)


class Phone(BaseModel):
    country_code: int
    number: int
    extension: int | None = None

    def as_str(self) -> str:
        ext_str = "ext. " + str(self.extension) if self.extension is not None else ""
        return " ".join((f"+{self.country_code}", str(self.number), ext_str))


class Contact(BaseModel, ToRdf):
    """Inspired by subset of https://schema.org/ContactPoint"""

    website: HttpUrl | None = None
    email: list[EmailStr] | None = Field(default=None, min_length=1)
    address: str | None = Field(default=None, min_length=1)
    phone: Phone | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "Contact":
        if self.website is None and self.email is None and self.address is None and self.phone is None:
            raise ValueError("Contact must have at least one field (website, email, address, or phone)")
        return self

    def to_rdf(self, g: Graph) -> BNode | None:
        if not self.email and not self.phone:
            return None  # will be an empty object

        contact = BNode()
        g.add((contact, RDF.type, SDO.ContactPoint))
        for e in self.email or ():
            g.add((contact, SDO.email, RdfLiteral(e)))
        if self.phone:
            g.add((contact, SDO.telephone, RdfLiteral(self.phone.as_str())))

        return contact


class Organization(BaseModel, ToRdf):
    type: Literal["organization"]
    name: str = Field(min_length=1)
    description: str | None = Field(default=None, min_length=1)
    contact: Contact | None = None
    location: str | None = Field(default=None, min_length=1)
    roles: list[RoleAnnotated] = Field(
        min_length=1,
        description=(
            "Role(s) this organization holds in relation to the work. It is good to include at least one "
            "DataCite-compatible role."
        ),
    )

    def to_rdf(self, g: Graph) -> BNode | None:
        org = BNode()
        g.add((org, RDF.type, SDO.Organization))
        g.add((org, SDO.name, RdfLiteral(self.name)))
        if self.description:
            g.add((org, SDO.name, RdfLiteral(self.description)))
        if self.contact and (c := self.contact.to_rdf(g)):
            g.add((org, SDO.contactPoint, c))
        return org


class Person(BaseModel, ToRdf):
    type: Literal["person"]
    name: str = Field(min_length=1)
    honorific: str | None = Field(default=None, min_length=1)
    other_names: list[str] | None = Field(
        default=None,
        min_length=1,
        description="Alternative names such as maiden names, nicknames, or transliterations",
    )
    affiliations: list[Organization | str] | None = Field(default=None, min_length=1)
    contact: Contact | None = None
    location: str | None = Field(default=None, min_length=1)
    orcid: Orcid | None = None
    roles: list[RoleAnnotated] = Field(
        default_factory=list,
        description=(
            "Role(s) this individual holds in relation to the work. It is good to include at least one "
            "DataCite-compatible role."
        ),
    )

    def to_rdf(self, g: Graph) -> BNode | None:
        person = BNode()
        g.add((person, RDF.type, FOAF.Person))
        g.add((person, RDF.type, SDO.Person))

        # Name
        g.add((person, FOAF.name, RdfLiteral(self.name)))
        g.add((person, SDO.name, RdfLiteral(self.name)))

        # Other names
        for on in self.other_names or ():
            g.add((person, SDO.alternateName, RdfLiteral(on)))

        # Affiliations
        for af in self.affiliations or ():
            if isinstance(af, Organization):
                org = af
            else:  # str
                org = Organization(type="organization", name=af, roles=[])
            if afn := org.to_rdf(g):
                g.add((person, SDO.affiliation, afn))

        # ORCID
        if self.orcid:
            g.add((person, SDO.sameAs, RdfLiteral(f"https://orcid.org/{self.orcid}")))

        # Honorifics
        if self.honorific:
            g.add((person, SDO.honorificPrefix, RdfLiteral(self.honorific)))

        # Contact information
        if self.contact and (c := self.contact.to_rdf(g)):
            g.add((person, SDO.contactPoint, c))

        return person


PersonOrOrganization = Annotated[Person | Organization, Field(discriminator="type")]


class ParticipantCriteria(BaseModel):
    link: HttpUrl | None = None
    type: ParticipantCriterionTypeAnnotated
    description: str = Field(min_length=1)


class Count(BaseModel):
    count_entity: str = Field(min_length=1)
    value: Annotated[float, BeforeValidator(float)]
    description: str = Field(min_length=1)


class License(BaseModel, ToRdf):
    """Derived from DCAT"""

    label: str = Field(min_length=1)
    type: str = Field(min_length=1)
    url: HttpUrl

    def to_rdf(self, g: Graph) -> BNode | URIRef | None:
        lic = URIRef(str(self.url))

        label = RdfLiteral(self.label)
        # Label/name/title
        g.add((lic, DCTERMS.title, label))
        g.add((lic, SDO.name, label))
        # License type
        g.add((lic, DCTERMS.type, RdfLiteral(self.type)))
        # License URL
        g.add((lic, SDO.url, RdfLiteral(self.url)))

        return lic


class PublicationVenue(BaseModel):
    """Where the publication was released or hosted (journal, conference, repository, or publisher)."""

    name: str = Field(min_length=1)
    venue_type: PublicationVenueTypeAnnotated | Other
    url: HttpUrl | None = None
    publisher: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None, min_length=1)


class Publication(BaseModel, ToRdf):
    """
    Publication or related resource link with metadata.
    """

    title: str = Field(min_length=1)
    url: HttpUrl
    doi: str | None = Field(default=None, min_length=1)
    publication_type: PublicationTypeAnnotated | Other
    authors: list[PersonOrOrganization] | None = Field(default=None, min_length=1)
    publication_date: date | None = None
    publication_venue: PublicationVenue | None = None
    description: str | None = Field(default=None, min_length=1)

    def to_rdf(self, g: Graph) -> BNode | None:
        pub = BNode()
        if self.publication_type in frozenset(
            (
                "Journal Article",
                "Review Article",
                "Conference Paper",
                "Workshop Paper",
                "Short Paper",
                "Preprint",
            )
        ):
            g.add((pub, RDF.type, SDO.ScholarlyArticle))
            for a in self.authors or ():
                if auth := a.to_rdf(g):
                    g.add((pub, SDO.author, auth))
            return pub
        else:
            return None  # Not mappable


class Logo(BaseModel):
    """
    Logo resource with optional theme-specific variants.

    Supports light/dark theme variants for optimal display across different UI themes.
    """

    url: AnyUrl
    theme: Literal["light", "dark", "default"] = "default"
    description: str | None = Field(default=None, min_length=1)
    contains_text: bool = Field(
        default=False, description="Whether the logo contains branding text to the left or right of the logo image."
    )


class SpatialCoverageProperties(BaseModel):
    """Properties for spatial coverage GeoJSON with required name field."""

    name: str = Field(min_length=1)
    model_config = ConfigDict(extra="allow")


class SpatialCoverageFeature(GeoJSONFeature):
    """GeoJSON Feature for spatial coverage with mandatory name in properties."""

    properties: SpatialCoverageProperties


class Link(BaseModel):
    """A labeled URL link."""

    label: str = Field(min_length=1)
    url: AnyUrl


class TypedLink(Link):
    """
    Related links to the dataset that are useful to reference in metadata.
    """

    type: LinkTypeAnnotated | Other


class FundingSource(BaseModel):
    """Funding source for the dataset/study."""

    funder: Annotated[str, Field(min_length=1)] | PersonOrOrganization | None = None
    grant_numbers: list[str] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_not_null(self) -> "FundingSource":
        if self.funder is None and self.grant_numbers is None:
            raise ValueError("FundingSource must have at least one of funder / grant number(s)")
        return self


class LongDescription(BaseModel):
    """Extended description with content type specification."""

    content: str = Field(min_length=1)
    content_type: Literal["text/html", "text/markdown", "text/plain"]


class DatasetModelBase(TranslatableModel):
    """Base dataset model without id field."""

    schema_version: Literal["1.0"]

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    long_description: LongDescription | None = None
    taxa: list[OntologyClass | str] | None = Field(default=None, min_length=1)

    keywords: list[str | OntologyClass] | None = Field(default=None, min_length=1)
    resources: list[VersionedOntologyResource] | None = Field(
        default=None,
        min_length=1,
        description="Ontology resources needed to resolve CURIEs in keywords and clinical/phenotypic data",
    )
    stakeholders: list[PersonOrOrganization] | None = Field(default=None, min_length=1)
    funding_sources: list[FundingSource | Link] | Annotated[str, Field(min_length=1)] | None = None

    spatial_coverage: Annotated[str, Field(min_length=1)] | SpatialCoverageFeature | None = None
    version: str | None = Field(default=None, min_length=1)
    privacy: str | None = Field(default=None, min_length=1)
    license: License | None = None
    counts: list[Count] | None = Field(default=None, min_length=1)
    primary_contact: PersonOrOrganization
    links: list[Link] | None = Field(default=None, min_length=1)
    publications: list[Publication] | None = Field(default=None, min_length=1)
    logos: list[Logo] | None = Field(default=None, min_length=1)
    release_date: date | None = None
    last_modified: date | None = None
    participant_criteria: list[ParticipantCriteria] | None = Field(default=None, min_length=1)

    study_status: Literal["ONGOING", "COMPLETED"] | None = None
    study_context: Literal["CLINICAL", "RESEARCH"] | None = None

    # Derived from the PCGL study model
    domain: list[str] | None = Field(
        default=None, min_length=1, description="List of specific scientific or clinical domains addressed by the study"
    )
    program_name: str | None = Field(
        None, min_length=1, description="The overarching program the study belongs to (if applicable)"
    )

    #  - PCGL-specific field: PCGL DAC ID
    pcgl_dac_id: str | None = Field(
        default=None,
        min_length=1,
        description="Unique identifier of the Data Access Committee (DAC) in PCGL to which the study is assigned",
    )

    # Discovery configuration specific to this dataset
    discovery: DiscoveryConfig | None = Field(
        default=None,
        description="Dataset-level discovery configuration; falls back to project/instance config if not set.",
    )

    # Extra properties: anything that doesn't fit elsewhere in the model
    extra_properties: dict[str, str | int | float | bool | None] | None = Field(
        None, description="Additional custom metadata properties not covered by the standard schema"
    )

    @model_validator(mode="after")
    def check_keyword_resources(self) -> "DatasetModelBase":
        resource_prefixes = {r.namespace_prefix for r in self.resources} if self.resources else set()

        if self.keywords:
            missing = sorted(
                {kw.id.split(":")[0] for kw in self.keywords if isinstance(kw, OntologyClass)} - resource_prefixes
            )
            if missing:
                raise ValueError(f"keywords contain OntologyClass CURIEs with no matching resource: {missing}")

        if self.taxa:
            missing = sorted(
                {t.id.split(":")[0] for t in self.taxa if isinstance(t, OntologyClass)} - resource_prefixes
            )
            if missing:
                raise ValueError(f"taxa contains OntologyClass CURIEs with no matching resource: {missing}")

        if self.stakeholders:
            missing_roles = [s.name for s in self.stakeholders if isinstance(s, Person) and not s.roles]
            if missing_roles:
                raise ValueError(f"stakeholder persons must have at least one role: {missing_roles}")

        return self


class DatasetModel(DatasetModelBase, ToRdf):
    """Dataset model with required identifier field."""

    identifier: str = Field(
        min_length=1, max_length=128
    )  # if from pcgl, directly inherited, otherwise created in katsu

    @classmethod
    def from_base(cls, base: DatasetModelBase, identifier: str) -> "DatasetModel":
        """Create a DatasetModel from a DatasetModelBase with the given identifier."""
        return cls(identifier=identifier, **base.model_dump())

    def to_rdf(self, g: Graph) -> BNode | None:
        keywords: list[RdfLiteral] = [
            RdfLiteral(kw.label, lang=self.language)
            if isinstance(kw, OntologyClass)
            else RdfLiteral(kw, lang=self.language)
            for kw in (self.keywords or ())
        ]

        funding: list[BNode] = []
        funders: list[BNode] = []  # non-grant funders

        for f in self.funding_sources or ():
            if isinstance(f, FundingSource):
                funder: BNode | None = None
                if isinstance(f.funder, (Organization, Person)):
                    funder = f.funder.to_rdf(g)
                elif isinstance(f.funder, str):
                    fndr = BNode()
                    g.add((fndr, RDF.type, SDO.Organization))
                    g.add((fndr, SDO.name, RdfLiteral(f.funder)))
                    funder = fndr

                if f.grant_numbers:  # Grant numbers; treat each one as a separate grant
                    for gn in f.grant_numbers:
                        grant = BNode()
                        g.add((grant, RDF.type, SDO.Grant))
                        g.add((grant, SDO.identifier, RdfLiteral(gn)))
                        if funder:
                            g.add((grant, SDO.funder, funder))
                        funding.append(grant)
                elif funder:  # Funder only, no grant numbers
                    funders.append(funder)

        ds = BNode()

        # purposefully don't map:
        #  - inLanguage - we don't know the language of the *contents* of the dataset

        # Type
        g.add((ds, RDF.type, DCAT.Dataset))
        g.add((ds, RDF.type, SDO.Dataset))

        # Name/title
        title = RdfLiteral(self.title, lang=self.language)
        g.add((ds, DCTERMS.title, title))
        g.add((ds, SDO.name, title))

        # Description
        if self.description:
            description = RdfLiteral(self.description, lang=self.language)
            g.add((ds, DCTERMS.description, description))
            g.add((ds, SDO.description, description))

        # Keywords
        for kw in keywords:
            g.add((ds, DCAT.keyword, kw))
            g.add((ds, SDO.keywords, kw))

        # Funders and funding
        for gr in funding:
            g.add((ds, SDO.funding, gr))  # not explicitly defined on namespace but still works with rdflib
        for f in funders:
            g.add((ds, SDO.funder, f))

        # License
        # TODO:

        # Modification date
        if last_modified := (RdfLiteral(self.last_modified.isoformat()) if self.last_modified else None):
            g.add((ds, DCTERMS.modified, last_modified))
            g.add((ds, SDO.dateModified, last_modified))

        # Dataset version
        if version := (RdfLiteral(self.version) if self.version else None):
            g.add((ds, DCAT.version, version))  # not explicitly defined on namespace but still works with rdflib
            g.add((ds, SDO.version, version))

        return ds


class ProjectScopedDatasetModel(DatasetModel):
    """Dataset model with an associated project field."""

    project: UUID

    @classmethod
    def from_base(cls, base: DatasetModelBase, identifier: str, project: UUID) -> "ProjectScopedDatasetModel":
        """Create a ProjectScopedDatasetModel from a DatasetModelBase with the given identifier and project."""
        return cls(identifier=identifier, project=project, **base.model_dump())

    @classmethod
    def from_dataset_model(cls, dataset: "DatasetModel", project: UUID) -> "ProjectScopedDatasetModel":
        """Create a ProjectScopedDatasetModel from a DatasetModel with the given project."""
        return cls(project=project, **dataset.model_dump())
