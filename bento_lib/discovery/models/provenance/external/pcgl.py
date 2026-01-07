"""
Pydantic models for PCGL (Pan Canadian Genomics Library) Study Schema
"""

__all__ = [
    "StudyStatus",
    "StudyContext",
    "StudyDomain",
    "PrincipalInvestigator",
    "Collaborator",
    "FundingSource",
    "Study",
]

from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict

# =============================================================================
# Enums and Literal Types
# =============================================================================
type StudyStatus = Literal["ONGOING", "COMPLETED"]
type StudyContext = Literal["CLINICAL", "RESEARCH"]
type StudyDomain = Literal[
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


# =============================================================================
# Supporting Classes
# =============================================================================
class PrincipalInvestigator(BaseModel):
    """
    A lead researcher responsible for the study.
    Format: Name, Affiliation
    """

    name: str = Field(..., description="Full name of the investigator")
    affiliation: str = Field(..., description="Institution or organization affiliation")


class Collaborator(BaseModel):
    """
    A researcher, institution, or company involved in the study.
    Format: Name, Role
    """

    name: str = Field(..., description="Name of individual or organization")
    role: str | None = Field(None, description="Role in the study (e.g., Industry Partner, Data Contributor)")


class FundingSource(BaseModel):
    """
    An organization or agency funding the study.
    Format: Funder name, Grant number
    """

    funder_name: str = Field(..., description="Name of the funding organization")
    grant_number: str | None = Field(None, description="Grant or award number")


# =============================================================================
# Main PCGL Study Class
# =============================================================================
class Study(BaseModel):
    """
    PCGL Study model - represents a genomics or clinical research study.
    This schema tracks comprehensive metadata about research studies including
    investigators, organizations, funding, and domain-specific information.
    """

    # =========================================================================
    # Core identification and descriptive fields
    # =========================================================================
    study_id: str = Field(..., alias="studyId", description="Unique identifier of the study in PCGL")
    study_name: str = Field(..., alias="studyName", description="The official name of the study")
    study_description: str = Field(
        ...,
        alias="studyDescription",
        description="A detailed description of the study's purpose, hypothesis, and design",
    )
    program_name: str | None = Field(
        None, alias="programName", description="The overarching program the study belongs to (if applicable)"
    )
    keywords: list[str] = Field(
        default_factory=list, description="list of specific terms that describe the focus and content of the study"
    )

    # =========================================================================
    # Study classification
    # =========================================================================

    status: StudyStatus = Field(..., description="Indicate if the study is completed or ongoing")
    context: StudyContext = Field(
        ..., description="Indicate if the study was conducted in a clinical setting or as part of a research project"
    )
    domain: list[StudyDomain] = Field(
        ..., min_length=1, description="list of specific scientific or clinical domains addressed by the study"
    )

    # =========================================================================
    # Data access and governance
    # =========================================================================

    dac_id: str = Field(
        ...,
        alias="dacId",
        description="Unique identifier of the Data Access Committee (DAC) in PCGL to which the study is assigned",
    )
    participant_criteria: str | None = Field(
        None,
        alias="participantCriteria",
        description="Inclusion/exclusion criteria for participants (e.g., specific cancer type, age range)",
    )

    # =========================================================================
    # People and organizations
    # =========================================================================

    principal_investigators: list[PrincipalInvestigator] = Field(
        ...,
        alias="principalInvestigators",
        min_length=1,
        description="list of lead researchers responsible for the study",
    )
    lead_organizations: list[str] = Field(
        ...,
        alias="leadOrganizations",
        min_length=1,
        description="list of institutions or organizations leading the study",
    )
    collaborators: list[Collaborator] = Field(
        default_factory=list, description="list of researchers, institutions or companies involved in the study"
    )

    # =========================================================================
    # Funding and publications
    # =========================================================================

    funding_sources: list[FundingSource] = Field(
        ..., alias="fundingSources", min_length=1, description="list of organizations or agencies funding the study"
    )
    publication_links: list[HttpUrl] = Field(
        default_factory=list,
        alias="publicationLinks",
        description="list of URL links to academic papers or reports associated with the study (DOI URLs)",
    )

    # =========================================================================
    # Configuration
    # =========================================================================

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("publication_links")
    @classmethod
    def validate_doi_links(cls, v: list[HttpUrl]) -> list[HttpUrl]:
        """Ensure publication links are DOI URLs"""
        for url in v:
            url_str = str(url)
            if not url_str.startswith("https://doi.org/"):
                raise ValueError(f"Publication link must be a DOI URL (https://doi.org/...): {url_str}")
        return v
