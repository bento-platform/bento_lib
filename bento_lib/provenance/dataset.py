__all__ = [
    "Role",
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
    "FundingSource",
    "LongDescription",
    "DatasetModel",
]

from typing import Annotated, Literal
from datetime import date
from pydantic import AnyUrl, BaseModel, BeforeValidator, EmailStr, Field, HttpUrl, ConfigDict
from geojson_pydantic import Feature as GeoJSONFeature

from bento_lib.ontologies.models import OntologyClass, VersionedOntologyResource
from bento_lib.i18n import TranslatableModel, TranslatedLiteral, EN, FR

Role = TranslatedLiteral(EN, FR)(
    # Leadership / oversight
    ("Principal Investigator",    "Chercheur principal"),
    ("Co-Investigator",           "Co-chercheur"),
    ("Sub-Investigator",          "Sous-chercheur"),
    ("Study Director",            "Directeur d'étude"),
    ("Project Lead",              "Chef de projet"),
    # Research team
    ("Researcher",                "Chercheur"),
    ("Research Assistant",        "Assistant de recherche"),
    ("Data Scientist",            "Scientifique des données"),
    ("Statistician",              "Statisticien"),
    ("Study Coordinator",         "Coordonnateur d'étude"),
    ("Lab Technician",            "Technicien de laboratoire"),
    # Participants / human subjects
    ("Participant",               "Participant"),
    ("Subject",                   "Sujet"),
    ("Volunteer",                 "Volontaire"),
    # Organizational / institutional roles
    ("Sponsoring Organization",   "Organisation commanditaire"),
    ("Collaborating Organization","Organisation collaboratrice"),
    ("Institution",               "Institution"),
    ("Site",                      "Site"),
    ("Research Center",           "Centre de recherche"),
    ("Publisher",                 "Éditeur"),
    # Ethics & compliance
    ("IRB",                       "CÉR"),
    ("Ethics Board",              "Comité d'éthique"),
    ("Data Monitoring Committee", "Comité de surveillance des données"),
    ("Compliance Officer",        "Responsable de la conformité"),
    # Funding & support
    ("Sponsor",                   "Commanditaire"),
    ("Funder",                    "Bailleur de fonds"),
    ("Grant Agency",              "Organisme subventionnaire"),
    # Contributors (non-research)
    ("Consultant",                "Consultant"),
    ("Advisor",                   "Conseiller"),
    ("Reviewer",                  "Évaluateur"),
    # Data & technical roles
    ("Data Provider",             "Fournisseur de données"),
    ("Data Controller",           "Responsable du traitement des données"),
    ("Data Processor",            "Sous-traitant des données"),
    ("Data Contributor",          "Contributeur de données"),
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
    # Reviews and other
    ("Survey",                 "Enquête"),
    ("Review Article",         "Article de synthèse"),
    ("Editorial",              "Éditorial"),
    ("Commentary",             "Commentaire"),
    ("Patent",                 "Brevet"),
)
PublicationTypeAnnotated = Annotated[str, PublicationType]

PublicationVenueType = TranslatedLiteral(EN, FR)(
    ("Journal",          "Revue"),
    ("Conference",       "Conférence"),
    ("Workshop",         "Atelier"),
    ("Repository",       "Dépôt"),
    ("Publisher",        "Éditeur"),
    ("University",       "Université"),
    ("Data Repository",  "Dépôt de données"),
)
PublicationVenueTypeAnnotated = Annotated[str, PublicationVenueType]

ParticipantCriterionType = TranslatedLiteral(EN, FR)(
    ("Inclusion", "Inclusion"),
    ("Exclusion", "Exclusion"),
)
ParticipantCriterionTypeAnnotated = Annotated[str, ParticipantCriterionType]

LinkType = TranslatedLiteral(EN, FR)(
    ("Downloadable Artifact",  "Artéfact téléchargeable"),
    ("Data Management Plan",   "Plan de gestion des données"),
    ("Schema",                 "Schéma"),
    ("External Reference",     "Référence externe"),
)
LinkTypeAnnotated = Annotated[str, LinkType]

class Other(BaseModel):
    """When a literal is not exhaustive"""

    other: str


class Phone(BaseModel):
    country_code: int
    number: int
    extension: int | None


class Contact(BaseModel):
    """Inspired by subset of https://schema.org/ContactPoint"""

    email: list[EmailStr]
    address: str | None
    phone: Phone | None


class Organization(BaseModel):
    name: str
    description: str | None
    contact: Contact
    roles: list[RoleAnnotated]


class Person(BaseModel):
    name: str
    honorific: str | None
    other_names: list[str] = Field(
        default_factory=list,
        description="Alternative names such as maiden names, nicknames, or transliterations",
    )

    affiliations: list[Organization | str]

    roles: list[RoleAnnotated]


class ParticipantCriteria(BaseModel):
    type: ParticipantCriterionTypeAnnotated
    description: str


class Count(BaseModel):
    count_entity: str
    value: Annotated[float, BeforeValidator(float)]
    description: str


class License(BaseModel):
    """Derived from DCAT"""

    label: str
    type: str
    url: HttpUrl


class PublicationVenue(BaseModel):
    """Where the publication was released or hosted (journal, conference, repository, or publisher)."""

    name: str
    venue_type: PublicationVenueTypeAnnotated | Other
    publisher: str | None
    location: str | None


class Publication(BaseModel):
    """
    Publication or related resource link with metadata.
    """

    title: str
    url: HttpUrl
    doi: str | None
    publication_type: PublicationTypeAnnotated | Other
    authors: list[Person | Organization]
    publication_date: date | None
    publication_venue: PublicationVenue | None
    description: str | None


class Logo(BaseModel):
    """
    Logo resource with optional theme-specific variants.

    Supports light/dark theme variants for optimal display across different UI themes.
    """

    url: AnyUrl
    theme: Literal["light", "dark", "default"] = "default"
    description: str | None = None


class SpatialCoverageProperties(BaseModel):
    """Properties for spatial coverage GeoJSON with required name field."""

    name: str

    model_config = ConfigDict(extra="allow")


class SpatialCoverageFeature(GeoJSONFeature):
    """GeoJSON Feature for spatial coverage with mandatory name in properties."""

    properties: SpatialCoverageProperties


class Link(BaseModel):
    """
    Related links to the dataset that are useful to reference in metadata.
    """

    label: str
    uri: AnyUrl
    type: LinkTypeAnnotated | Other


class FundingSource(BaseModel):
    """Funding source for the dataset/study."""

    funder: str | Organization | Person | None = None
    grant_numbers: list[str] = Field(default_factory=list)


class LongDescription(BaseModel):
    """Extended description with content type specification."""

    content: str
    content_type: Literal["text/html", "text/markdown", "text/plain"]


class DatasetModelBase(TranslatableModel):
    """Base dataset model without id field."""

    schema_version: Literal["1.0"]

    title: str
    description: str
    long_description: LongDescription | None = None

    keywords: list[str | OntologyClass]
    resources: list[VersionedOntologyResource] = Field(
        default_factory=list,
        description="Ontology resources needed to resolve CURIEs in keywords and clinical/phenotypic data",
    )
    stakeholders: list[Organization | Person]
    funding_sources: list[FundingSource] = Field(default_factory=list)

    spatial_coverage: str | SpatialCoverageFeature | None
    version: str | None
    privacy: str | None
    license: License | None
    counts: list[Count]  # Note: Different from counts in bento, this is provided by the metadata creator
    primary_contact: Person | Organization
    links: list[Link]
    publications: list[Publication]
    logos: list[Logo] = Field(default_factory=list)
    data_access_links: list[HttpUrl]
    release_date: date
    last_modified: date
    participant_criteria: list[ParticipantCriteria]

    # ----- Study Metadata -----
    study_status: Literal["ONGOING", "COMPLETED"] | None = None
    study_context: Literal["CLINICAL", "RESEARCH"] | None = None

    # ----- PCGL Specific -----
    pcgl_domain: list[str] = Field(
        ..., min_length=1, description="List of specific scientific or clinical domains addressed by the study"
    )
    pcgl_program_name: str | None = Field(
        None, description="The overarching program the study belongs to (if applicable)"
    )

    # ----- Additional Properties -----
    extra_properties: dict[str, str | int | float | bool | None] | None = Field(
        None, description="Additional custom metadata properties not covered by the standard schema"
    )


class DatasetModel(DatasetModelBase):
    """Dataset model with required id field."""

    id: str  # if from pcgl, directly inherited, otherwise created in katsu

    @classmethod
    def from_base(cls, base: DatasetModelBase, id: str) -> "DatasetModel":
        """Create a DatasetModel from a DatasetModelBase with the given id."""
        return cls(id=id, **base.model_dump())
