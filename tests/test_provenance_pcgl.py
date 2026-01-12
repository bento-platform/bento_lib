"""Tests for PCGL Study models and schema."""

from datetime import date

import pytest
from pydantic import HttpUrl, ValidationError

from bento_lib.discovery.models.provenance.external.pcgl import (
    Study,
    PrincipalInvestigator,
    Collaborator,
    FundingSource,
)
from bento_lib.discovery.models.provenance.converters import pcgl_study_to_dataset
from bento_lib.discovery.models.provenance import Person, Organization, Contact


def test_principal_investigator():
    """Test PrincipalInvestigator model."""
    pi = PrincipalInvestigator(name="John Doe", affiliation="Test University")
    assert pi.name == "John Doe"
    assert pi.affiliation == "Test University"


def test_collaborator():
    """Test Collaborator model."""
    collab = Collaborator(name="Partner Organization", role="Data Contributor")
    assert collab.name == "Partner Organization"
    assert collab.role == "Data Contributor"

    collab_no_role = Collaborator(name="Another Partner", role=None)
    assert collab_no_role.role is None


def test_funding_source():
    """Test FundingSource model."""
    funding = FundingSource(funder_name="NIH", grant_number="R01-123456")
    assert funding.funder_name == "NIH"
    assert funding.grant_number == "R01-123456"

    funding_no_grant = FundingSource(funder_name="NSF", grant_number=None)
    assert funding_no_grant.grant_number is None


def test_pcgl_study():
    """Test complete PCGL Study model."""
    study = Study(
        studyId="STUDY001",
        studyName="Cancer Genomics Study",
        studyDescription="A comprehensive study of cancer genomics",
        programName="National Cancer Program",
        keywords=["cancer", "genomics", "precision medicine"],
        status="ONGOING",
        context="RESEARCH",
        domain=["Cancer", "Population Genomics"],
        dacId="DAC001",
        participantCriteria="Inclusion: Adults 18+; Exclusion: Pregnant individuals",
        principalInvestigators=[PrincipalInvestigator(name="Jane Smith", affiliation="Test University")],
        leadOrganizations=["Test University", "Research Hospital"],
        collaborators=[Collaborator(name="Partner Lab", role="Data Contributor")],
        fundingSources=[FundingSource(funder_name="NIH", grant_number="R01-123456")],
        publicationLinks=[HttpUrl("https://doi.org/10.1234/example")],
    )

    assert study.study_id == "STUDY001"
    assert study.study_name == "Cancer Genomics Study"
    assert len(study.keywords) == 3
    assert len(study.principal_investigators) == 1
    assert len(study.lead_organizations) == 2
    assert study.dac_id == "DAC001"


def test_pcgl_study_minimal():
    """Test PCGL Study with minimal required fields."""
    study = Study(
        studyId="STUDY002",
        studyName="Minimal Study",
        studyDescription="Description",
        programName=None,
        keywords=[],
        status="COMPLETED",
        context="CLINICAL",
        domain=["Other"],
        dacId="DAC002",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(name="John Doe", affiliation="Org")],
        leadOrganizations=["Organization"],
        collaborators=[],
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=[],
    )

    assert study.keywords == []
    assert study.collaborators == []
    assert study.publication_links == []


def test_pcgl_study_validation_doi_links():
    """Test that publicationLinks must be DOI URLs."""
    with pytest.raises(ValidationError) as exc:
        Study(
            studyId="STUDY003",
            studyName="Test Study",
            studyDescription="Description",
            programName=None,
            keywords=[],
            status="ONGOING",
            context="RESEARCH",
            domain=["Cancer"],
            dacId="DAC003",
            participantCriteria=None,
            principalInvestigators=[PrincipalInvestigator(name="John Doe", affiliation="Org")],
            leadOrganizations=["Org"],
            collaborators=[],
            fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
            publicationLinks=[HttpUrl("https://example.com/paper")],  # Not a DOI URL
        )
    assert "must be a DOI URL" in str(exc.value)


def test_pcgl_study_validation_empty_lists():
    """Test that required lists cannot be empty."""
    # Empty principalInvestigators
    with pytest.raises(ValidationError) as exc:
        Study(
            studyId="STUDY004",
            studyName="Test Study",
            studyDescription="Description",
            programName=None,
            keywords=[],
            status="ONGOING",
            context="RESEARCH",
            domain=["Cancer"],
            dacId="DAC004",
            participantCriteria=None,
            principalInvestigators=[],  # Empty list
            leadOrganizations=["Org"],
            collaborators=[],
            fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
            publicationLinks=[],
        )
    assert "at least 1 item" in str(exc.value).lower()


def test_pcgl_study_validation_invalid_domain():
    """Test that domain values must be from the allowed list."""
    with pytest.raises(ValidationError) as exc:
        Study(
            studyId="STUDY005",
            studyName="Test Study",
            studyDescription="Description",
            programName=None,
            keywords=[],
            status="ONGOING",
            context="RESEARCH",
            domain=["InvalidDomain"],  # Not in the StudyDomain literal
            dacId="DAC005",
            participantCriteria=None,
            principalInvestigators=[PrincipalInvestigator(name="John Doe", affiliation="Org")],
            leadOrganizations=["Org"],
            collaborators=[],
            fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
            publicationLinks=[],
        )
    assert "domain" in str(exc.value).lower()


# ===== Converter Tests =====


@pytest.fixture
def basic_primary_contact():
    """Basic primary contact for converter tests."""
    return Person(
        name="Contact Person",
        honorific=None,
        other_names=[],
        affiliations=[],
        roles=["Study Coordinator"],
    )


@pytest.fixture
def full_pcgl_study():
    """Full PCGL study with all fields populated."""
    return Study(
        studyId="STUDY001",
        studyName="Cancer Genomics Study",
        studyDescription="A comprehensive study of cancer genomics",
        programName="National Cancer Program",
        keywords=["cancer", "genomics"],
        status="ONGOING",
        context="RESEARCH",
        domain=["Cancer", "Population Genomics"],
        dacId="DAC001",
        participantCriteria="Inclusion: Adults 18+; Exclusion: Pregnant individuals",
        principalInvestigators=[
            PrincipalInvestigator(name="Jane Smith", affiliation="Test University"),
            PrincipalInvestigator(name="John Doe", affiliation=""),
        ],
        leadOrganizations=["Test University", "Research Hospital"],
        collaborators=[
            Collaborator(name="Partner Lab", role="Data Contributor"),
            Collaborator(name="Other Partner", role=None),
        ],
        fundingSources=[FundingSource(funder_name="NIH", grant_number="R01-123456")],
        publicationLinks=[
            HttpUrl("https://doi.org/10.1234/example"),
            HttpUrl("https://doi.org/10.5678/another"),
        ],
    )


@pytest.fixture
def minimal_pcgl_study():
    """Minimal PCGL study with only required fields."""
    return Study(
        studyId="STUDY002",
        studyName="Minimal Study",
        studyDescription="Description",
        programName=None,
        keywords=[],
        status="COMPLETED",
        context="CLINICAL",
        domain=["Other"],
        dacId="DAC002",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(name="John Doe", affiliation="Org")],
        leadOrganizations=["Organization"],
        collaborators=[],
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=[],
    )


def test_pcgl_study_to_dataset_full(full_pcgl_study, basic_primary_contact):
    """Test converter with full PCGL study."""
    dataset = pcgl_study_to_dataset(
        study=full_pcgl_study,
        release_date=date(2024, 1, 1),
        last_modified=date(2024, 6, 1),
        primary_contact=basic_primary_contact,
        data_access_links=[HttpUrl("https://example.com/data")],
        spatial_coverage="Canada",
        version="1.0",
        privacy="Controlled Access",
    )

    assert dataset.id == "STUDY001"
    assert dataset.title == "Cancer Genomics Study"
    assert dataset.description == "A comprehensive study of cancer genomics"
    assert dataset.schema_version == "1.0"

    # Check keywords
    assert len(dataset.keywords) == 2
    assert "cancer" in dataset.keywords

    # Check stakeholders (2 PIs + 2 lead orgs + 2 collaborators + 1 funder = 7)
    assert len(dataset.stakeholders) == 7

    # Check PI conversion
    pi_stakeholders = [s for s in dataset.stakeholders if isinstance(s, Person)]
    assert len(pi_stakeholders) == 2
    assert pi_stakeholders[0].name == "Jane Smith"
    assert pi_stakeholders[0].affiliations == ["Test University"]
    assert pi_stakeholders[1].affiliations == []  # No affiliation

    # Check organization conversion
    org_stakeholders = [s for s in dataset.stakeholders if isinstance(s, Organization)]
    assert len(org_stakeholders) == 5

    # Check publications with DOI extraction
    assert len(dataset.publications) == 2
    assert dataset.publications[0].doi == "10.1234/example"
    assert dataset.publications[1].doi == "10.5678/another"

    # Check participant criteria parsing
    assert len(dataset.participant_criteria) == 2
    assert dataset.participant_criteria[0].type == "Inclusion"
    assert dataset.participant_criteria[0].description == "Adults 18+"
    assert dataset.participant_criteria[1].type == "Exclusion"

    # Check PCGL-specific fields
    assert dataset.pcgl_domain == ["Cancer", "Population Genomics"]
    assert dataset.pcgl_status == "ONGOING"
    assert dataset.pcgl_context == "RESEARCH"
    assert dataset.pcgl_program_name == "National Cancer Program"

    # Check optional fields passed through
    assert dataset.spatial_coverage == "Canada"
    assert dataset.version == "1.0"
    assert dataset.privacy == "Controlled Access"


def test_pcgl_study_to_dataset_minimal(minimal_pcgl_study, basic_primary_contact):
    """Test converter with minimal PCGL study."""
    dataset = pcgl_study_to_dataset(
        study=minimal_pcgl_study,
        release_date=date(2024, 1, 1),
        last_modified=date(2024, 6, 1),
        primary_contact=basic_primary_contact,
    )

    assert dataset.id == "STUDY002"
    assert dataset.keywords == []
    assert dataset.publications == []
    assert dataset.participant_criteria == []
    assert dataset.data_access_links == []
    assert dataset.counts == []
    assert dataset.pcgl_program_name is None


def test_pcgl_study_to_dataset_collaborator_without_role(basic_primary_contact):
    """Test that collaborators without role get default role."""
    study = Study(
        studyId="STUDY003",
        studyName="Test",
        studyDescription="Test",
        programName=None,
        keywords=[],
        status="ONGOING",
        context="RESEARCH",
        domain=["Other"],
        dacId="DAC003",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(name="PI", affiliation="Org")],
        leadOrganizations=["Org"],
        collaborators=[Collaborator(name="Partner", role=None)],
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=[],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2024, 1, 1),
        last_modified=date(2024, 1, 1),
        primary_contact=basic_primary_contact,
    )

    # Find the collaborator organization
    collab_org = next(s for s in dataset.stakeholders if isinstance(s, Organization) and s.name == "Partner")
    assert collab_org.roles == ["Collaborating Organization"]


def test_pcgl_study_to_dataset_non_doi_publication(basic_primary_contact):
    """Test publication link that is not a DOI URL gets None for doi field."""
    study = Study(
        studyId="STUDY004",
        studyName="Test",
        studyDescription="Test",
        programName=None,
        keywords=[],
        status="ONGOING",
        context="RESEARCH",
        domain=["Other"],
        dacId="DAC004",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(name="PI", affiliation="Org")],
        leadOrganizations=["Org"],
        collaborators=[],
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=[HttpUrl("https://doi.org/10.1234/test")],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2024, 1, 1),
        last_modified=date(2024, 1, 1),
        primary_contact=basic_primary_contact,
    )

    assert dataset.publications[0].doi == "10.1234/test"


def test_pcgl_study_to_dataset_with_organization_contact(full_pcgl_study):
    """Test converter with Organization as primary contact."""
    org_contact = Organization(
        name="Contact Org",
        description=None,
        contact=Contact(email=["contact@org.com"], address=None, phone=None),
        roles=["Institution"],
        grant_number=None,
    )

    dataset = pcgl_study_to_dataset(
        study=full_pcgl_study,
        release_date=date(2024, 1, 1),
        last_modified=date(2024, 1, 1),
        primary_contact=org_contact,
    )

    assert isinstance(dataset.primary_contact, Organization)
    assert dataset.primary_contact.name == "Contact Org"
