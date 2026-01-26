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
    "DatasetModel",
]

from typing import Annotated, Literal
from datetime import date
from pydantic import AnyUrl, BaseModel, BeforeValidator, EmailStr, Field, HttpUrl, ConfigDict
from geojson_pydantic import Feature as GeoJSONFeature

from bento_lib.ontologies.models import OntologyClass, VersionedOntologyResource


type Role = Literal[
    # Leadership / oversight
    "Principal Investigator",
    "Co-Investigator",
    "Sub-Investigator",
    "Study Director",
    "Project Lead",
    # Research team
    "Researcher",
    "Research Assistant",
    "Data Scientist",
    "Statistician",
    "Study Coordinator",
    "Lab Technician",
    # Participants / human subjects
    "Participant",
    "Subject",
    "Volunteer",
    # Organizational / institutional roles
    "Sponsoring Organization",
    "Collaborating Organization",
    "Institution",
    "Site",
    "Research Center",
    "Publisher",  # DCAT
    # Ethics & compliance
    "IRB",
    "Ethics Board",
    "Data Monitoring Committee",
    "Compliance Officer",
    # Funding & support
    "Sponsor",
    "Funder",
    "Grant Agency",
    # Contributors (non-research)
    "Consultant",
    "Advisor",
    "Reviewer",
    # Data & technical roles
    "Data Provider",
    "Data Controller",
    "Data Processor",
    "Data Contributor",
    # External stakeholders
    "Partner",
    "Stakeholder",
    "Community Representative",
    "Other",
]

type PublicationType = Literal[
    # Articles and papers
    "Journal Article",
    "Conference Paper",
    "Workshop Paper",
    "Short Paper",
    "Poster",
    "Preprint",
    # Books and long form
    "Book",
    "Book Chapter",
    "Monograph",
    # Reports and gray literature
    "Technical Report",
    "White Paper",
    "Working Paper",
    # Academic qualifications
    "Thesis",
    "Master's Thesis",
    "Doctoral Dissertation",
    # Data and software
    "Dataset",
    "Software",
    "Software Paper",
    # Reviews and other
    "Survey",
    "Review Article",
    "Editorial",
    "Commentary",
    "Patent",
]

type PublicationVenueType = Literal[
    "Journal",
    "Conference",
    "Workshop",
    "Repository",
    "Publisher",
    "University",
    "Data Repository",
]


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
    roles: list[Role]


class Person(BaseModel):
    name: str
    honorific: str | None
    other_names: list[str] = Field(
        default_factory=list,
        description="Alternative names such as maiden names, nicknames, or transliterations",
    )

    affiliations: list[Organization | str]

    roles: list[Role]


class ParticipantCriteria(BaseModel):
    type: Literal["Inclusion", "Exclusion"]
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
    venue_type: PublicationVenueType | Other
    publisher: str | None
    location: str | None


class Publication(BaseModel):
    """
    Publication or related resource link with metadata.
    """

    title: str
    url: HttpUrl
    doi: str | None
    publication_type: PublicationType | Other
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
    type: Literal["Downloadable Artifact", "Data Management Plan", "Schema", "External Reference"] | Other


class FundingSource(BaseModel):
    """Funding source for the dataset/study."""

    funder: str | Organization | Person | None = None
    grant_numbers: list[str] = Field(default_factory=list)


class DatasetModelBase(BaseModel):
    """Base dataset model without id field."""

    schema_version: Literal["1.0"]

    title: str
    description: str

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
