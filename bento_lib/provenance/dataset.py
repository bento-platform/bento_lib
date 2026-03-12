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
    "TypedLink",
    "FundingSource",
    "LongDescription",
    "PersonOrOrganization",
    "DatasetModel",
    "ProjectScopedDatasetModel",
]

from typing import Annotated, Literal
from datetime import date
from uuid import UUID
from pydantic import AnyUrl, BaseModel, BeforeValidator, EmailStr, Field, HttpUrl, ConfigDict, model_validator
from geojson_pydantic import Feature as GeoJSONFeature

from bento_lib.ontologies.models import OntologyClass, VersionedOntologyResource
from bento_lib.i18n import TranslatableModel, TranslatedLiteral, EN, FR

# Turning formating off to preserve columnar structure
# fmt: off
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
    ("Consortium",                "Consortium"),
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


class Contact(BaseModel):
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


class Organization(BaseModel):
    type: Literal["organization"]
    name: str = Field(min_length=1)
    description: str | None = Field(default=None, min_length=1)
    contact: Contact | None = None
    location: str | None = Field(default=None, min_length=1)
    roles: list[RoleAnnotated] = Field(min_length=1)


class Person(BaseModel):
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
    roles: list[RoleAnnotated] = Field(min_length=1)


PersonOrOrganization = Annotated[Person | Organization, Field(discriminator="type")]


class ParticipantCriteria(BaseModel):
    link: HttpUrl | None = None
    type: ParticipantCriterionTypeAnnotated
    description: str = Field(min_length=1)


class Count(BaseModel):
    count_entity: str = Field(min_length=1)
    value: Annotated[float, BeforeValidator(float)]
    description: str = Field(min_length=1)


class License(BaseModel):
    """Derived from DCAT"""

    label: str = Field(min_length=1)
    type: str = Field(min_length=1)
    url: HttpUrl


class PublicationVenue(BaseModel):
    """Where the publication was released or hosted (journal, conference, repository, or publisher)."""

    name: str = Field(min_length=1)
    venue_type: PublicationVenueTypeAnnotated | Other
    url: HttpUrl | None = None
    publisher: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None, min_length=1)


class Publication(BaseModel):
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


class Logo(BaseModel):
    """
    Logo resource with optional theme-specific variants.

    Supports light/dark theme variants for optimal display across different UI themes.
    """

    url: AnyUrl
    theme: Literal["light", "dark", "default"] = "default"
    description: str | None = Field(default=None, min_length=1)
    contains_text: bool = Field(default=False, description="Whether the logo contains branding text to the left or right of the logo image.")


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

    funder: str | PersonOrOrganization | None = Field(default=None, min_length=1)
    grant_numbers: list[str] | None = Field(default=None, min_length=1)


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
    taxonomy: list[OntologyClass | str] | None = None

    keywords: list[str | OntologyClass] | None = Field(default=None, min_length=1)
    resources: list[VersionedOntologyResource] | None = Field(
        default=None,
        min_length=1,
        description="Ontology resources needed to resolve CURIEs in keywords and clinical/phenotypic data",
    )
    stakeholders: list[PersonOrOrganization] = Field(min_length=1)
    funding_sources: list[FundingSource | Link] | Annotated[str, Field(min_length=1)] | None = None

    spatial_coverage: str | SpatialCoverageFeature | None = Field(default=None, min_length=1)
    version: str | None = Field(default=None, min_length=1)
    privacy: str | None = Field(default=None, min_length=1)
    license: License | None = None
    counts: list[Count] | None = Field(default=None, min_length=1)
    primary_contact: PersonOrOrganization
    links: list[Link] = Field(min_length=1)
    publications: list[Publication] | None = Field(default=None, min_length=1)
    logos: list[Logo] | None = Field(default=None, min_length=1)
    release_date: date | None = None
    last_modified: date | None = None
    participant_criteria: list[ParticipantCriteria] | None = Field(default=None, min_length=1)

    study_status: Literal["ONGOING", "COMPLETED"] | None = None
    study_context: Literal["CLINICAL", "RESEARCH"] | None = None

    pcgl_domain: list[str] | None = Field(
        default=None, min_length=1, description="List of specific scientific or clinical domains addressed by the study"
    )
    pcgl_program_name: str | None = Field(
        None, min_length=1, description="The overarching program the study belongs to (if applicable)"
    )

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

        if self.taxonomy:
            missing = sorted(
                {t.id.split(":")[0] for t in self.taxonomy if isinstance(t, OntologyClass)} - resource_prefixes
            )
            if missing:
                raise ValueError(f"taxonomy contains OntologyClass CURIEs with no matching resource: {missing}")

        return self


class DatasetModel(DatasetModelBase):
    """Dataset model with required identifier field."""

    identifier: str = Field(
        min_length=1, max_length=128
    )  # if from pcgl, directly inherited, otherwise created in katsu

    @classmethod
    def from_base(cls, base: DatasetModelBase, identifier: str) -> "DatasetModel":
        """Create a DatasetModel from a DatasetModelBase with the given identifier."""
        return cls(identifier=identifier, **base.model_dump())


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
