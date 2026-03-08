"""Tests for PCGL Study to DatasetModel converter."""

from datetime import date

from bento_lib.provenance import Organization, Person
from bento_lib.provenance.dataset import Count, Link
from bento_lib.provenance.converters.pcgl import _parse_participant_criteria, pcgl_study_to_dataset


def test_parse_participant_criteria():
    assert _parse_participant_criteria(None) is None
    assert _parse_participant_criteria("") is None

    criteria_str = "Inclusion: Adults 18+; Exclusion: Pregnant individuals"
    result = _parse_participant_criteria(criteria_str)
    assert len(result) == 1
    assert result[0].type == "Other"
    assert result[0].description == criteria_str


def test_pcgl_study_to_dataset(pcgl_study_full, basic_pi):
    """Test converting PCGL Study to DatasetModel."""
    dataset = pcgl_study_to_dataset(
        study=pcgl_study_full,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        primary_contact=basic_pi,
        counts=[Count(count_entity="participants", value=100, description="Number of participants")],
        links=[
            Link(label="Study Link", url="https://example.com/study", type="Schema"),
            Link(label="Data Access", url="https://example.com/data", type="Data Access"),
        ],
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

    # Check participant criteria (PCGL string wrapped as a single Other-typed entry)
    assert len(dataset.participant_criteria) == 1
    assert dataset.participant_criteria[0].description == "Inclusion: Adults 18+; Exclusion: Pregnant individuals"

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
    assert nsf_funder.grant_numbers is None  # NSF had null grant_number

    # Check publications
    assert len(dataset.publications) == 2
    assert str(dataset.publications[0].url) == "https://doi.org/10.1234/example"
    assert dataset.publications[0].doi == "10.1234/example"


def test_pcgl_study_to_dataset_minimal(pcgl_study_minimal, basic_pi):
    """Test conversion with minimal study (Other domain, minimal criteria)."""
    dataset = pcgl_study_to_dataset(
        study=pcgl_study_minimal,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=basic_pi,
        counts=[Count(count_entity="participants", value=0, description="Number of participants")],
        links=[
            Link(label="Study Link", url="https://example.com/study", type="Schema"),
            Link(label="Data Access", url="https://example.com/data", type="Data Access"),
        ],
    )

    assert len(dataset.pcgl_domain) == 1
    assert dataset.pcgl_domain[0] == "Other"
    assert dataset.study_status == "COMPLETED"
    assert dataset.study_context == "CLINICAL"
