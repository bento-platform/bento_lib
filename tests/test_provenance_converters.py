"""Tests for PCGL Study to DatasetModel converter."""

from datetime import date

from bento_lib.provenance import Organization, Person
from bento_lib.provenance.converters.pcgl import (
    pcgl_study_to_dataset,
    _parse_participant_criteria,
)


def test_pcgl_study_to_dataset(pcgl_study_full, basic_pi):
    """Test converting PCGL Study to DatasetModel."""
    dataset = pcgl_study_to_dataset(
        study=pcgl_study_full,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        primary_contact=basic_pi,
    )

    assert dataset.title == "Cancer Study"
    assert dataset.description == "A cancer genomics study"
    assert dataset.pcgl_program_name == "Cancer Program"
    assert dataset.keywords == ["cancer", "genomics"]
    assert dataset.study_status == "ONGOING"
    assert dataset.study_context == "RESEARCH"
    assert dataset.pcgl_domain[0] == "Cancer"
    assert dataset.pcgl_domain[1] == "Population Genomics"
    assert dataset.release_date == date(2023, 1, 1)
    assert dataset.last_modified == date(2023, 6, 1)

    # Check participant criteria parsing
    assert len(dataset.participant_criteria) == 2
    assert dataset.participant_criteria[0].type == "Inclusion"
    assert dataset.participant_criteria[0].description == "Adults 18+"
    assert dataset.participant_criteria[1].type == "Exclusion"
    assert dataset.participant_criteria[1].description == "Pregnant individuals"

    # Check stakeholders (1 PI, 2 institutions, 2 collaborators = 5 total)
    assert len(dataset.stakeholders) == 5

    # Find PI (parsed from "Jane Smith")
    pis = [s for s in dataset.stakeholders if isinstance(s, Person) and "Principal Investigator" in s.roles]
    assert len(pis) == 1
    assert pis[0].name == "Jane Smith"

    # Find institutions
    institutions = [s for s in dataset.stakeholders if isinstance(s, Organization) and "Institution" in s.roles]
    assert len(institutions) == 2
    assert {inst.name for inst in institutions} == {"Test University", "Research Hospital"}

    # Check funding sources - should be grouped by funder name
    assert len(dataset.funding_sources) == 2  # NIH and NSF grouped
    funders = {f.funder for f in dataset.funding_sources}
    assert "NIH" in funders
    assert "NSF" in funders
    nih_funder = next(f for f in dataset.funding_sources if f.funder == "NIH")
    assert nih_funder.grant_numbers == ["R01-123456", "R01-789012"]  # Both NIH grants consolidated
    nsf_funder = next(f for f in dataset.funding_sources if f.funder == "NSF")
    assert nsf_funder.grant_numbers == []  # NSF had null grant_number

    # Check publications
    assert len(dataset.publications) == 2
    assert str(dataset.publications[0].url) == "https://doi.org/10.1234/example"
    assert dataset.publications[0].doi == "10.1234/example"


def test_pcgl_study_to_dataset_minimal(pcgl_study_minimal, basic_pi):
    """Test conversion with minimal study (Other domain, no criteria)."""
    dataset = pcgl_study_to_dataset(
        study=pcgl_study_minimal,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=basic_pi,
    )

    assert len(dataset.pcgl_domain) == 1
    assert dataset.pcgl_domain[0] == "Other"
    assert dataset.participant_criteria == []
    assert dataset.study_status == "COMPLETED"
    assert dataset.study_context == "CLINICAL"


def test_parse_participant_criteria_malformed():
    """Test parsing participant criteria with malformed strings."""
    assert _parse_participant_criteria("Inclusion Adults 18+") == []  # Missing colon
    assert _parse_participant_criteria("InvalidType: Some description") == []  # Invalid type

    # Mixed valid and invalid
    result = _parse_participant_criteria("Inclusion: Valid; InvalidType: Invalid; Exclusion: Also valid")
    assert len(result) == 2
    assert result[0].type == "Inclusion"
    assert result[1].type == "Exclusion"
