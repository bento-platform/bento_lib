"""Tests for DatasetModel<->PCGL Study converters."""

import pytest
from datetime import date
from pydantic import HttpUrl

from bento_lib.discovery.models.ontology import OntologyTerm
from bento_lib.discovery.models.provenance import (
    DatasetModel,
    Contact,
    Count,
    License,
    Organization,
    ParticipantCriteria,
    Person,
    Publication,
)
from bento_lib.discovery.models.provenance.external.pcgl import (
    Study,
    PrincipalInvestigator,
    Collaborator,
    FundingSource,
)
from bento_lib.discovery.models.provenance.converters.pcgl import (
    dataset_to_pcgl_study,
    pcgl_study_to_dataset,
    _parse_participant_criteria,
)


def test_dataset_to_pcgl_study(basic_pi, basic_contact):
    """Test converting DatasetModel to PCGL Study."""
    institution = Organization(
        name="Test University",
        description="Research institution",
        contact=basic_contact,
        roles=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="NIH",
        description=None,
        contact=basic_contact,
        roles=["Funder"],
        grant_number="R01-123456",
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Cancer Study",
        description="A cancer genomics study",
        keywords=["cancer", "genomics"],
        stakeholders=[basic_pi, institution, funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        publications=[
            Publication(
                title="Results",
                url=HttpUrl("https://doi.org/10.1234/test"),
                doi="10.1234/test",
                publication_type="Journal Article",
                authors=None,
                publication_date=None,
                journal=None,
                description=None,
            )
        ],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        participant_criteria=[
            ParticipantCriteria(type="Inclusion", description="Adults 18+"),
            ParticipantCriteria(type="Exclusion", description="Pregnant individuals"),
        ],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name="Cancer Genomics Program",
    )

    study = dataset_to_pcgl_study(dataset, study_id="STUDY001", dac_id="DAC001")

    assert study.study_id == "STUDY001"
    assert study.study_name == "Cancer Study"
    assert study.study_description == "A cancer genomics study"
    assert study.program_name == "Cancer Genomics Program"
    assert study.keywords == ["cancer", "genomics"]
    assert study.status == "ONGOING"
    assert study.context == "RESEARCH"
    assert study.domain == ["Cancer"]
    assert study.dac_id == "DAC001"
    assert study.participant_criteria == "Inclusion: Adults 18+; Exclusion: Pregnant individuals"
    assert len(study.principal_investigators) == 1
    assert study.principal_investigators[0].name == "Jane Doe"
    assert len(study.lead_organizations) == 1
    assert "Test University" in study.lead_organizations
    assert len(study.funding_sources) == 1
    assert study.funding_sources[0].funder_name == "NIH"
    assert study.funding_sources[0].grant_number == "R01-123456"
    assert len(study.publication_links) == 1
    assert str(study.publication_links[0]) == "https://doi.org/10.1234/test"


def test_dataset_to_pcgl_study_with_ontology_keywords(basic_pi, basic_institution, basic_funder, minimal_dataset):
    """Test conversion with OntologyTerm keywords (should extract labels)."""
    minimal_dataset.keywords = [
        "plain keyword",
        OntologyTerm(id="HP:0001250", label="Seizure"),
    ]
    study = dataset_to_pcgl_study(minimal_dataset, study_id="S001", dac_id="D001")
    assert study.keywords == ["plain keyword", "Seizure"]


def test_dataset_to_pcgl_study_with_other_domain(basic_pi, basic_institution, basic_funder, minimal_dataset):
    """Test conversion with Other domain."""
    minimal_dataset.domain = ["Other"]
    minimal_dataset.status = "COMPLETED"
    minimal_dataset.context = "CLINICAL"

    study = dataset_to_pcgl_study(minimal_dataset, study_id="S001", dac_id="D001")
    assert study.domain == ["Other"]


def test_dataset_to_pcgl_study_missing_pi(basic_contact):
    """Test that conversion fails if no Principal Investigator found."""
    researcher = Person(
        name="John Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        roles=["Researcher"],
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[
            researcher,
            Organization(
                name="Test Org", description=None, contact=basic_contact, roles=["Institution"], grant_number=None
            ),
            Organization(name="Funder", description=None, contact=basic_contact, roles=["Funder"], grant_number=None),
        ],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=researcher,
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name=None,
    )

    with pytest.raises(ValueError) as exc:
        dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert "No principal investigators found" in str(exc.value)


def test_dataset_to_pcgl_study_missing_organization(basic_pi, basic_contact):
    """Test that conversion fails if no lead organization found."""
    funder = Organization(
        name="Funder",
        description=None,
        contact=basic_contact,
        roles=["Funder"],
        grant_number=None,
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[basic_pi, funder],  # No institution
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name=None,
    )

    with pytest.raises(ValueError) as exc:
        dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert "No lead organizations found" in str(exc.value)


def test_dataset_to_pcgl_study_missing_funder(basic_pi, basic_institution):
    """Test that conversion fails if no funding source found."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[basic_pi, basic_institution],  # No funder
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name=None,
    )

    with pytest.raises(ValueError) as exc:
        dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert "No funding sources found" in str(exc.value)


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


@pytest.mark.parametrize(
    "pi_config,expected_affiliation",
    [
        ({"affiliations": [], "name_parts": ("Bob", "Smith")}, ""),  # Empty affiliations
        (
            {
                "affiliations": [
                    Organization(
                        name="Research Institute",
                        description=None,
                        contact=Contact(email=[], address=None, phone=None),
                        roles=["Institution"],
                        grant_number=None,
                    )
                ],
                "name_parts": ("Alice", "Johnson"),
            },
            "Research Institute",
        ),  # Org affiliation
        ({"affiliations": ["University Name"], "name_parts": ("John", "Doe")}, "University Name"),  # String affiliation
    ],
)
def test_converter_pi_affiliation_extraction(basic_contact, pi_config, expected_affiliation):
    """Test PI affiliation extraction from various sources."""
    pi = Person(
        name=f"{pi_config['name_parts'][0]} {pi_config['name_parts'][1]}",
        honorific=None,
        other_names=[],
        affiliations=pi_config["affiliations"],
        roles=["Principal Investigator"],
    )
    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[
            pi,
            Organization(
                name="Test Org", description=None, contact=basic_contact, roles=["Institution"], grant_number=None
            ),
            Organization(name="Funder", description=None, contact=basic_contact, roles=["Funder"], grant_number=None),
        ],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=pi,
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name=None,
    )
    study = dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert study.principal_investigators[0].affiliation == expected_affiliation


def test_converter_stakeholder_roles(basic_contact, basic_pi):
    """Test comprehensive stakeholder extraction: multiple org types, collaborators (Person/Org), and funders (Person/Org)."""
    # All stakeholder types in one test to reduce duplication
    institutions = [
        Organization(
            name="University", description=None, contact=basic_contact, roles=["Institution"], grant_number=None
        ),
        Organization(
            name="Research Center",
            description=None,
            contact=basic_contact,
            roles=["Research Center"],
            grant_number=None,
        ),
        Organization(name="Clinical Site", description=None, contact=basic_contact, roles=["Site"], grant_number=None),
    ]
    researcher = Person(name="Alice Smith", honorific=None, other_names=[], affiliations=[], roles=["Researcher"])
    collab_org = Organization(
        name="Partner Lab",
        description=None,
        contact=basic_contact,
        roles=["Collaborating Organization"],
        grant_number=None,
    )
    org_funder = Organization(
        name="Grant Agency", description=None, contact=basic_contact, roles=["Grant Agency"], grant_number="GA-123"
    )
    person_funder = Person(
        name="John Philanthropist", honorific=None, other_names=[], affiliations=[], roles=["Funder"]
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Desc",
        keywords=[],
        stakeholders=[basic_pi, *institutions, researcher, collab_org, org_funder, person_funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name=None,
    )

    study = dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")

    # Verify lead organizations (3 types)
    assert len(study.lead_organizations) == 3
    assert set(study.lead_organizations) == {"University", "Research Center", "Clinical Site"}

    # Verify collaborators (Person + Org, not leadership orgs)
    assert study.collaborators is not None
    assert len(study.collaborators) == 2
    collab_names = {c.name for c in study.collaborators}
    assert "Alice Smith" in collab_names
    assert "Partner Lab" in collab_names

    # Verify funders (Org + Person)
    assert len(study.funding_sources) == 2
    funder_names = {f.funder_name for f in study.funding_sources}
    assert "Grant Agency" in funder_names
    assert "John Philanthropist" in funder_names
    org_funder_obj = next(f for f in study.funding_sources if f.funder_name == "Grant Agency")
    assert org_funder_obj.grant_number == "GA-123"
    person_funder_obj = next(f for f in study.funding_sources if f.funder_name == "John Philanthropist")
    assert person_funder_obj.grant_number is None


def test_converter_publications_and_optional_params(basic_pi, basic_contact):
    """Test DOI publication filtering and optional conversion parameters."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Desc",
        keywords=[],
        stakeholders=[
            basic_pi,
            Organization(
                name="Univ", description=None, contact=basic_contact, roles=["Institution"], grant_number=None
            ),
            Organization(name="Funder", description=None, contact=basic_contact, roles=["Funder"], grant_number=None),
        ],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        publications=[
            Publication(
                title="DOI Paper",
                url=HttpUrl("https://doi.org/10.1234/doi"),
                doi="10.1234/doi",
                publication_type="Journal Article",
                authors=None,
                publication_date=None,
                journal=None,
                description=None,
            ),
            Publication(
                title="Non-DOI",
                url=HttpUrl("https://example.com/paper"),
                doi=None,
                publication_type="Preprint",
                authors=None,
                publication_date=None,
                journal=None,
                description=None,
            ),
        ],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=["Cancer"],
        status="ONGOING",
        context="RESEARCH",
        program_name=None,
    )

    # Test non-DOI filtering
    study = dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert len(study.publication_links) == 1
    assert str(study.publication_links[0]) == "https://doi.org/10.1234/doi"

    # Test pcgl_study_to_dataset with optional params
    license_obj = License(
        label="CC BY 4.0", type="Creative Commons", url=HttpUrl("https://creativecommons.org/licenses/by/4.0/")
    )
    dataset2 = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=basic_pi,
        data_access_links=[HttpUrl("https://example.com/data")],
        spatial_coverage="Canada",
        version="2.0",
        privacy="Controlled",
        license=license_obj,
        counts=[Count(count_entity="samples", value=500, description="Total samples")],
    )
    assert dataset2.spatial_coverage == "Canada"
    assert dataset2.version == "2.0"
    assert dataset2.privacy == "Controlled"
    assert dataset2.license == license_obj
    assert len(dataset2.counts) == 1
    assert len(dataset2.data_access_links) == 1
    assert dataset2.keywords == []  # None keywords becomes empty list


def test_parse_participant_criteria_malformed():
    """Test parsing participant criteria with malformed strings."""
    assert _parse_participant_criteria("Inclusion Adults 18+") == []  # Missing colon
    assert _parse_participant_criteria("InvalidType: Some description") == []  # Invalid type

    # Mixed valid and invalid
    result = _parse_participant_criteria("Inclusion: Valid; InvalidType: Invalid; Exclusion: Also valid")
    assert len(result) == 2
    assert result[0].type == "Inclusion"
    assert result[1].type == "Exclusion"


def test_dataset_to_pcgl_study_invalid_domain(basic_pi, basic_institution, basic_funder, minimal_dataset):
    """Test that conversion fails with invalid domain values."""
    from pydantic import ValidationError

    minimal_dataset.domain = ["Invalid Domain Value"]

    with pytest.raises(ValidationError) as exc:
        dataset_to_pcgl_study(minimal_dataset, study_id="S001", dac_id="D001")
    assert "domain" in str(exc.value).lower()
