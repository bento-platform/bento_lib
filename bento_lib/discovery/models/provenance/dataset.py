from typing import Literal
from datetime import date
from pydantic import BaseModel, HttpUrl, ConfigDict
from geojson_pydantic import Feature as GeoJSONFeature


Role = Literal[
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
    # External stakeholders
    "Partner",
    "Stakeholder",
    "Community Representative",
    "Other",
]

# Derived from PCGL Study Model
StudyDomain = Literal[
    "Aging",
    "Birth Defects",
    "Cancer",
    "Circulatory and Respiratory Health",
    "General Health",
    "Infection and Immunity",
    "Musculoskeletal Health and Arthritis",
    "Neurodevelopmental Conditions",
    "Neurosciences, Mental Health and Addiction",
    "Nutrition, Metabolism and Diabetes",
    "Population Genomics",
    "Rare Diseases",
    "Other",
]


class Phone(BaseModel):
    country_code: int
    number: int
    extension: int | None


class Contact(BaseModel):
    email: list[str]
    address: str | None
    phone: Phone | None


class Organization(BaseModel):
    name: str
    description: str | None
    contact: Contact
    role: list[Role]

    # For funders
    grant_number: str | None


class Person(BaseModel):
    first_name: str
    last_name: str
    honorific: str | None
    other_names: list[str]

    affiliations: list[Organization | str]

    role: list[Role]


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
    url: HttpUrl | None


class SpatialCoverageProperties(BaseModel):
    """Properties for spatial coverage GeoJSON with required name field."""

    name: str

    model_config = ConfigDict(extra="allow")


class SpatialCoverageFeature(GeoJSONFeature):
    """GeoJSON Feature for spatial coverage with mandatory name in properties."""

    properties: SpatialCoverageProperties


class DatasetModel(BaseModel):
    schema_version_: Literal["1.0"]

    title: str
    description: str

    keywords: list[str]
    stakeholders: list[Organization | Person]

    spatial_coverage: str | SpatialCoverageFeature | None
    version: str | None
    privacy: str | None
    license: License | None
    counts: list[Count]
    primary_contact: Person | Organization

    publication_links: list[HttpUrl]
    data_access_links: list[HttpUrl]
    release_data: date
    last_modified: date
    participant_criteria: list[ParticipantCriteria]

    # ----- PCGL Specific -----
    domain: list[StudyDomain]
    status: Literal["Ongoing", "Completed"]
    context: Literal["Clinical", "Research"]
    program_name: str | None
