"""Tests for PCGL Study to DatasetModel converter."""

from datetime import date
from pydantic import HttpUrl

from bento_lib.discovery.models.provenance import (
    Organization,
    Person,
)
from bento_lib.discovery.models.provenance.external.pcgl import (
    Study,
    PrincipalInvestigator,
    Collaborator,
    FundingSource,
)
from bento_lib.discovery.models.provenance.converters.pcgl import (
    pcgl_study_to_dataset,
    _parse_participant_criteria,
)


def test_pcgl_study_to_dataset(basic_pi):
    """Test converting PCGL Study to DatasetModel."""
    study = Study(
        studyId="STUDY001",
        studyName="Cancer Study",
        studyDescription="A cancer genomics study",
        programName="Cancer Program",
        keywords=["cancer", "genomics"],
        status="ONGOING",
        context="RESEARCH",
        domain=["Cancer", "Population Genomics"],
        dacId="DAC001",
        participantCriteria="Inclusion: Adults 18+; Exclusion: Pregnant individuals",
        principalInvestigators=[PrincipalInvestigator(name="Jane Smith", affiliation="Test University")],
        leadOrganizations=["Test University", "Research Hospital"],
        collaborators=[
            Collaborator(name="Partner Lab", role="Data Contributor"),
            Collaborator(name="Another Partner", role=None),
        ],
        fundingSources=[
            FundingSource(funder_name="NIH", grant_number="R01-123456"),
            FundingSource(funder_name="NSF", grant_number=None),
        ],
        publicationLinks=[
            HttpUrl("https://doi.org/10.1234/example"),
            HttpUrl("https://doi.org/10.5678/another"),
        ],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        primary_contact=basic_pi,
    )

    assert dataset.title == "Cancer Study"
    assert dataset.description == "A cancer genomics study"
    assert dataset.program_name == "Cancer Program"
    assert dataset.keywords == ["cancer", "genomics"]
    assert dataset.status == "ONGOING"
    assert dataset.context == "RESEARCH"
    assert dataset.domain[0] == "Cancer"
    assert dataset.domain[1] == "Population Genomics"
    assert dataset.release_date == date(2023, 1, 1)
    assert dataset.last_modified == date(2023, 6, 1)

    # Check participant criteria parsing
    assert len(dataset.participant_criteria) == 2
    assert dataset.participant_criteria[0].type == "Inclusion"
    assert dataset.participant_criteria[0].description == "Adults 18+"
    assert dataset.participant_criteria[1].type == "Exclusion"
    assert dataset.participant_criteria[1].description == "Pregnant individuals"

    # Check stakeholders (1 PI, 2 institutions, 2 collaborators, 2 funders = 7 total)
    assert len(dataset.stakeholders) == 7

    # Find PI (parsed from "Jane Smith")
    pis = [s for s in dataset.stakeholders if isinstance(s, Person) and "Principal Investigator" in s.roles]
    assert len(pis) == 1
    assert pis[0].name == "Jane Smith"

    # Find institutions
    institutions = [s for s in dataset.stakeholders if isinstance(s, Organization) and "Institution" in s.roles]
    assert len(institutions) == 2
    assert {inst.name for inst in institutions} == {"Test University", "Research Hospital"}

    # Find funders
    funders = [s for s in dataset.stakeholders if isinstance(s, Organization) and "Funder" in s.roles]
    assert len(funders) == 2
    funder_names = {f.name for f in funders}
    assert "NIH" in funder_names
    assert "NSF" in funder_names
    nih_funder = next(f for f in funders if f.name == "NIH")
    assert nih_funder.grant_number == "R01-123456"

    # Check publications
    assert len(dataset.publications) == 2
    assert str(dataset.publications[0].url) == "https://doi.org/10.1234/example"
    assert dataset.publications[0].doi == "10.1234/example"


def test_pcgl_study_to_dataset_with_other_domain(basic_pi):
    """Test conversion with Other domain."""
    study = Study(
        studyId="STUDY002",
        studyName="Other Study",
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

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=basic_pi,
    )

    assert len(dataset.domain) == 1
    assert dataset.domain[0] == "Other"


def test_pcgl_study_to_dataset_no_criteria(basic_pi):
    """Test conversion with no participant criteria."""
    study = Study(
        studyId="STUDY003",
        studyName="Study",
        studyDescription="Description",
        programName=None,
        keywords=[],
        status="ONGOING",
        context="RESEARCH",
        domain=["Cancer"],
        dacId="DAC003",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(name="John Doe", affiliation="Org")],
        leadOrganizations=["Organization"],
        collaborators=[],
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=[],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=basic_pi,
    )

    assert dataset.participant_criteria == []


def test_parse_participant_criteria_malformed():
    """Test parsing participant criteria with malformed strings."""
    assert _parse_participant_criteria("Inclusion Adults 18+") == []  # Missing colon
    assert _parse_participant_criteria("InvalidType: Some description") == []  # Invalid type

    # Mixed valid and invalid
    result = _parse_participant_criteria("Inclusion: Valid; InvalidType: Invalid; Exclusion: Also valid")
    assert len(result) == 2
    assert result[0].type == "Inclusion"
    assert result[1].type == "Exclusion"
