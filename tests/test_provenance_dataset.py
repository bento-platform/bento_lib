"""Tests for DatasetModel and roundtrip conversions."""

from datetime import date
from pydantic import HttpUrl, ValidationError
import pytest
from geojson_pydantic import Point

from bento_lib.discovery.models.ontology import OntologyTerm
from bento_lib.discovery.models.provenance import (
    DatasetModel,
    Contact,
    Count,
    License,
    Organization,
    ParticipantCriteria,
    Publication,
    Other,
    SpatialCoverageFeature,
    SpatialCoverageProperties,
)
from bento_lib.discovery.models.provenance.converters.pcgl import (
    dataset_to_pcgl_study,
    pcgl_study_to_dataset,
)


def test_dataset_model(basic_pi, basic_contact):
    """Test complete DatasetModel."""
    institution = Organization(
        name="Test University",
        description="Research institution",
        contact=Contact(email=["contact@test.edu"], address=None, phone=None),
        roles=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="National Science Foundation",
        description=None,
        contact=basic_contact,
        roles=["Funder"],
        grant_number="NSF-12345",
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="A comprehensive test study",
        keywords=["genomics", "cancer"],
        stakeholders=[basic_pi, institution, funder],
        spatial_coverage="Canada",
        version="1.0",
        privacy="Controlled Access",
        license=License(
            label="CC BY 4.0", type="Creative Commons", url=HttpUrl("https://creativecommons.org/licenses/by/4.0/")
        ),
        counts=[Count(count_entity="participants", value=100, description="Total participants")],
        primary_contact=basic_pi,
        publications=[
            Publication(
                title="Study Results",
                url=HttpUrl("https://doi.org/10.1234/test"),
                doi="10.1234/test",
                publication_type="Journal Article",
                authors=None,
                publication_date=None,
                journal=None,
                description=None,
            )
        ],
        data_access_links=[HttpUrl("https://example.com/data")],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        participant_criteria=[ParticipantCriteria(type="Inclusion", description="Adults 18+")],
        domain=["Cancer"],
        status="Ongoing",
        context="Research",
        program_name="Cancer Genomics Program",
    )

    assert dataset.title == "Test Study"
    assert len(dataset.stakeholders) == 3
    assert dataset.status == "Ongoing"
    assert dataset.context == "Research"
    assert dataset.domain[0] == "Cancer"


def test_dataset_model_with_other_domain(basic_pi):
    """Test DatasetModel with Other domain."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        keywords=[],
        stakeholders=[basic_pi],
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
        domain=[Other(other="Custom Domain")],
        status="Ongoing",
        context="Research",
        program_name=None,
    )

    assert isinstance(dataset.domain[0], Other)
    assert dataset.domain[0].other == "Custom Domain"


def test_dataset_model_with_ontology_keywords(basic_pi):
    """Test DatasetModel with OntologyTerm keywords."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        keywords=[
            "plain keyword",
            OntologyTerm(id="HP:0001250", label="Seizure"),
            OntologyTerm(id="MONDO:0005015", label="Diabetes mellitus"),
        ],
        stakeholders=[basic_pi],
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
        status="Completed",
        context="Clinical",
        program_name=None,
    )

    assert len(dataset.keywords) == 3
    assert dataset.keywords[0] == "plain keyword"
    assert isinstance(dataset.keywords[1], OntologyTerm)
    assert dataset.keywords[1].id == "HP:0001250"


def test_dataset_model_validation_domain_required(basic_pi):
    """Test that domain is required and must have at least one item."""
    with pytest.raises(ValidationError) as exc:
        DatasetModel(
            schema_version="1.0",
            title="Test Study",
            description="Test",
            keywords=[],
            stakeholders=[basic_pi],
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
            domain=[],  # Empty domain should fail
            status="Ongoing",
            context="Research",
            program_name=None,
        )
    assert "at least 1 item" in str(exc.value).lower()


def test_dataset_model_with_spatial_coverage_feature(basic_pi):
    """Test DatasetModel with SpatialCoverageFeature."""
    spatial_feature = SpatialCoverageFeature(
        type="Feature",
        geometry=Point(type="Point", coordinates=[-79.3832, 43.6532]),
        properties=SpatialCoverageProperties(name="Toronto, Canada"),
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Toronto Study",
        description="A study conducted in Toronto",
        keywords=[],
        stakeholders=[basic_pi],
        spatial_coverage=spatial_feature,
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
        status="Ongoing",
        context="Research",
        program_name=None,
    )

    assert isinstance(dataset.spatial_coverage, SpatialCoverageFeature)
    assert dataset.spatial_coverage.properties.name == "Toronto, Canada"


def test_roundtrip_conversion(basic_pi, basic_contact):
    """Test converting Dataset -> Study -> Dataset maintains core information."""
    original_institution = Organization(
        name="Test University",
        description="Research institution",
        contact=Contact(email=["contact@test.edu"], address=None, phone=None),
        roles=["Institution"],
        grant_number=None,
    )

    original_funder = Organization(
        name="NIH",
        description=None,
        contact=basic_contact,
        roles=["Funder"],
        grant_number="R01-123456",
    )

    original_dataset = DatasetModel(
        schema_version="1.0",
        title="Cancer Study",
        description="A cancer genomics study",
        keywords=["cancer", "genomics"],
        stakeholders=[basic_pi, original_institution, original_funder],
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
        ],
        domain=["Cancer"],
        status="Ongoing",
        context="Research",
        program_name="Cancer Program",
    )

    # Convert to Study
    study = dataset_to_pcgl_study(original_dataset, study_id="STUDY001", dac_id="DAC001")

    # Convert back to Dataset
    roundtrip_dataset = pcgl_study_to_dataset(
        study=study,
        release_date=original_dataset.release_date,
        last_modified=original_dataset.last_modified,
        primary_contact=basic_pi,
    )

    # Check core fields maintained
    assert roundtrip_dataset.title == original_dataset.title
    assert roundtrip_dataset.description == original_dataset.description
    assert roundtrip_dataset.keywords == original_dataset.keywords
    assert roundtrip_dataset.status == original_dataset.status
    assert roundtrip_dataset.context == original_dataset.context
    assert roundtrip_dataset.domain == original_dataset.domain
    assert roundtrip_dataset.program_name == original_dataset.program_name
    assert len(roundtrip_dataset.participant_criteria) == len(original_dataset.participant_criteria)
    assert len(roundtrip_dataset.publications) == len(original_dataset.publications)
