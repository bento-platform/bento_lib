"""Tests for PCGL Study models and schema."""

import pytest
from pydantic import HttpUrl, ValidationError

from bento_lib.discovery.models.provenance.external.pcgl import (
    Study,
    PrincipalInvestigator,
    Collaborator,
    FundingSource,
)


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
        status="Ongoing",
        context="Research",
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
        status="Completed",
        context="Clinical",
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
            status="Ongoing",
            context="Research",
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
            status="Ongoing",
            context="Research",
            domain=["Cancer"],
            dacId="DAC004",
            participalCriteria=None,
            principalInvestigators=[],  # Empty list
            leadOrganizations=["Org"],
            collaborators=[],
            fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
            publicationLinks=[],
        )
    assert "at least 1 item" in str(exc.value).lower()
