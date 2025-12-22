from typing import Literal
from datetime import date
from pydantic import AnyUrl, BaseModel, Field, HttpUrl, ConfigDict
from geojson_pydantic import Feature as GeoJSONFeature

from bento_lib.discovery.models.ontology import OntologyTerm


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
    "Poster Paper",
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

    email: list[str]
    address: str | None
    phone: Phone | None


class Organization(BaseModel):
    name: str
    description: str | None
    contact: Contact
    roles: list[Role]

    # For funders
    grant_number: str | None


class Person(BaseModel):
    name: str
    honorific: str | None
    other_names: list[str]

    affiliations: list[Organization | str]

    roles: list[Role]


class ParticipantCriteria(BaseModel):
    type: Literal["Inclusion", "Exclusion"]
    description: str


class Count(BaseModel):
    count_entity: str
    value: int | float
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
    authors: list["Person | Organization"] | None
    publication_date: date | None
    publication_venue: PublicationVenue | None
    description: str | None


class Logo(BaseModel):
    """
    Logo resource with optional theme-specific variants.

    Supports light/dark theme variants for optimal display across different UI themes.
    """

    url: AnyUrl
    theme: Literal["light", "dark", "default"] | None = None
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


class DatasetModel(BaseModel):
    schema_version: Literal["1.0"]

    title: str
    description: str
    dataset_id: str  # if from pcgl, directly inheritied, otherwise created in katsu

    keywords: list[str | OntologyTerm]
    stakeholders: list[Organization | Person]

    spatial_coverage: str | SpatialCoverageFeature | None
    version: str | None
    privacy: str | None
    license: License | None
    counts: list[Count]  # Note: Different from counts in bento, this is provided by the metadata creator
    primary_contact: Person | Organization
    links: list[Link]
    publications: list[Publication]
    logos: list[Logo] | None = None
    data_access_links: list[HttpUrl]
    release_date: date
    last_modified: date
    participant_criteria: list[ParticipantCriteria]

    # ----- PCGL Specific -----
    pcgl_domain: list[str] = Field(
        ..., min_length=1, description="List of specific scientific or clinical domains addressed by the study"
    )
    pcgl_status: Literal["ONGOING", "COMPLETED"]
    pcgl_context: Literal["CLINICAL", "RESEARCH"]
    pcgl_program_name: str | None = Field(
        None, description="The overarching program the study belongs to (if applicable)"
    )

    # ----- Additional Properties -----
    extra_properties: dict[str, str | int | float | bool | None] | None = Field(
        None, description="Additional custom metadata properties not covered by the standard schema"
    )
