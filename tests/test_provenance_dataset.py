"""Tests for DatasetModel."""

from datetime import date
from pydantic import HttpUrl, ValidationError
import pytest
from geojson_pydantic import Point

from bento_lib.ontologies.models import OntologyClass
from bento_lib.discovery.models.provenance import (
    DatasetModel,
    Contact,
    Count,
    License,
    Logo,
    Organization,
    ParticipantCriteria,
    Publication,
    SpatialCoverageFeature,
    SpatialCoverageProperties,
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
        dataset_id="test-study-001",
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
        links=[],
        publications=[
            Publication(
                title="Study Results",
                url=HttpUrl("https://doi.org/10.1234/test"),
                doi="10.1234/test",
                publication_type="Journal Article",
                authors=None,
                publication_date=None,
                publication_venue=None,
                description=None,
            )
        ],
        data_access_links=[HttpUrl("https://example.com/data")],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        participant_criteria=[ParticipantCriteria(type="Inclusion", description="Adults 18+")],
        pcgl_domain=["Cancer"],
        pcgl_status="ONGOING",
        pcgl_context="RESEARCH",
        pcgl_program_name="Cancer Genomics Program",
    )

    assert dataset.title == "Test Study"
    assert len(dataset.stakeholders) == 3
    assert dataset.pcgl_status == "ONGOING"
    assert dataset.pcgl_context == "RESEARCH"
    assert dataset.pcgl_domain[0] == "Cancer"


def test_dataset_model_with_custom_domain(basic_pi):
    """Test DatasetModel with custom domain string."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        dataset_id="test-study-002",
        keywords=[],
        stakeholders=[basic_pi],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        links=[],
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        pcgl_domain=["Custom Domain"],
        pcgl_status="ONGOING",
        pcgl_context="RESEARCH",
        pcgl_program_name=None,
    )

    assert dataset.pcgl_domain[0] == "Custom Domain"


def test_dataset_model_with_ontology_keywords(basic_pi):
    """Test DatasetModel with OntologyClass keywords."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        dataset_id="test-study-003",
        keywords=[
            "plain keyword",
            OntologyClass(id="HP:0001250", label="Seizure"),
            OntologyClass(id="MONDO:0005015", label="Diabetes mellitus"),
        ],
        stakeholders=[basic_pi],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        links=[],
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        pcgl_domain=["Cancer"],
        pcgl_status="COMPLETED",
        pcgl_context="CLINICAL",
        pcgl_program_name=None,
    )

    assert len(dataset.keywords) == 3
    assert dataset.keywords[0] == "plain keyword"
    assert isinstance(dataset.keywords[1], OntologyClass)
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
            links=[],
            publications=[],
            data_access_links=[],
            release_date=date(2023, 1, 1),
            last_modified=date(2023, 1, 1),
            participant_criteria=[],
            pcgl_domain=[],  # Empty domain should fail
            pcgl_status="ONGOING",
            pcgl_context="RESEARCH",
            pcgl_program_name=None,
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
        dataset_id="test-study-004",
        keywords=[],
        stakeholders=[basic_pi],
        spatial_coverage=spatial_feature,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        links=[],
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        pcgl_domain=["Cancer"],
        pcgl_status="ONGOING",
        pcgl_context="RESEARCH",
        pcgl_program_name=None,
    )

    assert isinstance(dataset.spatial_coverage, SpatialCoverageFeature)
    assert dataset.spatial_coverage.properties.name == "Toronto, Canada"


def test_dataset_model_with_logos(basic_pi):
    """Test DatasetModel with Logo support."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        dataset_id="test-study-005",
        keywords=[],
        stakeholders=[basic_pi],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        links=[],
        publications=[],
        logos=[
            Logo(
                url=HttpUrl("https://example.com/logo-light.png"),
                theme="light",
                description="Light theme logo",
            ),
            Logo(
                url=HttpUrl("https://example.com/logo-dark.png"),
                theme="dark",
                description="Dark theme logo",
            ),
        ],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        pcgl_domain=["Cancer"],
        pcgl_status="ONGOING",
        pcgl_context="RESEARCH",
        pcgl_program_name=None,
    )

    assert dataset.logos is not None
    assert len(dataset.logos) == 2
    assert dataset.logos[0].theme == "light"
    assert dataset.logos[1].theme == "dark"
    assert dataset.logos[0].url == HttpUrl("https://example.com/logo-light.png")
    assert dataset.logos[1].url == HttpUrl("https://example.com/logo-dark.png")


def test_dataset_model_with_extra_properties(basic_pi):
    """Test DatasetModel with extra_properties for custom metadata."""
    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        dataset_id="test-study-006",
        keywords=[],
        stakeholders=[basic_pi],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=basic_pi,
        links=[],
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        pcgl_domain=["Cancer"],
        pcgl_status="ONGOING",
        pcgl_context="RESEARCH",
        pcgl_program_name=None,
        extra_properties={
            "custom_field": "custom_value",
            "sample_size": 1000,
            "is_multi_site": True,
            "completion_rate": 87.5,
        },
    )

    assert dataset.extra_properties is not None
    assert dataset.extra_properties["custom_field"] == "custom_value"
    assert dataset.extra_properties["sample_size"] == 1000
    assert dataset.extra_properties["is_multi_site"] is True
    assert dataset.extra_properties["completion_rate"] == 87.5
