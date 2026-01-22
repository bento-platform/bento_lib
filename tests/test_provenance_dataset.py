"""Tests for DatasetModel."""

import json
from datetime import date
from pathlib import Path

from pydantic import HttpUrl, ValidationError
import pytest
from geojson_pydantic import Point

from bento_lib.ontologies.models import OntologyClass, VersionedOntologyResource
from bento_lib.provenance import (
    DatasetModel,
    DatasetModelBase,
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

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_dataset_model(base_dataset_kwargs, basic_pi, basic_contact):
    """Test complete DatasetModel with all fields populated."""
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
        **{
            **base_dataset_kwargs,
            "description": "A comprehensive test study",
            "keywords": ["genomics", "cancer"],
            "stakeholders": [basic_pi, institution, funder],
            "spatial_coverage": "Canada",
            "version": "1.0",
            "privacy": "Controlled Access",
            "license": License(
                label="CC BY 4.0",
                type="Creative Commons",
                url=HttpUrl("https://creativecommons.org/licenses/by/4.0/"),
            ),
            "counts": [Count(count_entity="participants", value=100, description="Total participants")],
            "publications": [
                Publication(
                    title="Study Results",
                    url=HttpUrl("https://doi.org/10.1234/test"),
                    doi="10.1234/test",
                    publication_type="Journal Article",
                    authors=[],
                    publication_date=None,
                    publication_venue=None,
                    description=None,
                )
            ],
            "data_access_links": [HttpUrl("https://example.com/data")],
            "last_modified": date(2023, 6, 1),
            "participant_criteria": [ParticipantCriteria(type="Inclusion", description="Adults 18+")],
            "pcgl_program_name": "Cancer Genomics Program",
        }
    )

    assert dataset.title == "Test Study"
    assert len(dataset.stakeholders) == 3
    assert dataset.study_status == "ONGOING"
    assert dataset.study_context == "RESEARCH"
    assert dataset.pcgl_domain[0] == "Cancer"


def test_dataset_model_with_custom_domain(base_dataset_kwargs):
    """Test DatasetModel with custom domain string."""
    dataset = DatasetModel(
        **{
            **base_dataset_kwargs,
            "id": "test-study-002",
            "pcgl_domain": ["Custom Domain"],
        }
    )

    assert dataset.pcgl_domain[0] == "Custom Domain"


def test_dataset_model_with_ontology_keywords(base_dataset_kwargs):
    """Test DatasetModel with OntologyClass keywords."""
    dataset = DatasetModel(
        **{
            **base_dataset_kwargs,
            "id": "test-study-003",
            "keywords": [
                "plain keyword",
                OntologyClass(id="HP:0001250", label="Seizure"),
                OntologyClass(id="MONDO:0005015", label="Diabetes mellitus"),
            ],
            "study_status": "COMPLETED",
            "study_context": "CLINICAL",
        }
    )

    assert len(dataset.keywords) == 3
    assert dataset.keywords[0] == "plain keyword"
    assert isinstance(dataset.keywords[1], OntologyClass)
    assert dataset.keywords[1].id == "HP:0001250"


def test_dataset_model_validation_domain_required(base_dataset_kwargs):
    """Test that domain is required and must have at least one item."""
    with pytest.raises(ValidationError) as exc:
        DatasetModel(**{**base_dataset_kwargs, "pcgl_domain": []})
    assert "at least 1 item" in str(exc.value).lower()


def test_dataset_model_with_spatial_coverage_feature(base_dataset_kwargs):
    """Test DatasetModel with SpatialCoverageFeature."""
    spatial_feature = SpatialCoverageFeature(
        type="Feature",
        geometry=Point(type="Point", coordinates=[-79.3832, 43.6532]),
        properties=SpatialCoverageProperties(name="Toronto, Canada"),
    )

    dataset = DatasetModel(
        **{
            **base_dataset_kwargs,
            "title": "Toronto Study",
            "description": "A study conducted in Toronto",
            "id": "test-study-004",
            "spatial_coverage": spatial_feature,
        }
    )

    assert isinstance(dataset.spatial_coverage, SpatialCoverageFeature)
    assert dataset.spatial_coverage.properties.name == "Toronto, Canada"


def test_dataset_model_with_logos(base_dataset_kwargs):
    """Test DatasetModel with Logo support."""
    logos = [
        Logo(url=HttpUrl("https://example.com/logo-light.png"), theme="light", description="Light theme logo"),
        Logo(url=HttpUrl("https://example.com/logo-dark.png"), theme="dark", description="Dark theme logo"),
    ]

    dataset = DatasetModel(**{**base_dataset_kwargs, "id": "test-study-005", "logos": logos})

    assert dataset.logos is not None
    assert len(dataset.logos) == 2
    assert dataset.logos[0].theme == "light"
    assert dataset.logos[1].theme == "dark"
    assert dataset.logos[0].url == HttpUrl("https://example.com/logo-light.png")
    assert dataset.logos[1].url == HttpUrl("https://example.com/logo-dark.png")


def test_dataset_model_with_extra_properties(base_dataset_kwargs):
    """Test DatasetModel with extra_properties for custom metadata."""
    extra_props = {
        "custom_field": "custom_value",
        "sample_size": 1000,
        "is_multi_site": True,
        "completion_rate": 87.5,
    }

    dataset = DatasetModel(**{**base_dataset_kwargs, "id": "test-study-006", "extra_properties": extra_props})

    assert dataset.extra_properties is not None
    assert dataset.extra_properties["custom_field"] == "custom_value"
    assert dataset.extra_properties["sample_size"] == 1000
    assert dataset.extra_properties["is_multi_site"] is True
    assert dataset.extra_properties["completion_rate"] == 87.5


def test_dataset_model_from_base(base_dataset_kwargs):
    """Test creating DatasetModel from DatasetModelBase using from_base."""
    # Remove id from kwargs since DatasetModelBase doesn't have it
    base_kwargs = {k: v for k, v in base_dataset_kwargs.items() if k != "id"}
    base = DatasetModelBase(**base_kwargs)

    dataset = DatasetModel.from_base(base, id="new-dataset-id")

    assert dataset.id == "new-dataset-id"
    assert dataset.title == base.title
    assert dataset.description == base.description
    assert dataset.schema_version == base.schema_version
    assert dataset.pcgl_domain == base.pcgl_domain


def test_count_value_converts_int_to_float():
    """Test that Count.value converts int to float."""
    count = Count(count_entity="participants", value=100, description="Total participants")
    assert count.value == 100.0
    assert isinstance(count.value, float)


def test_dataset_model_resources_default_empty(base_dataset_kwargs):
    """Test that resources defaults to empty list."""
    dataset = DatasetModel(**base_dataset_kwargs)
    assert dataset.resources == []


def test_dataset_model_with_resources(base_dataset_kwargs):
    """Test DatasetModel with VersionedOntologyResource for CURIE resolution."""
    resource = VersionedOntologyResource(
        id="hp",
        name="Human Phenotype Ontology",
        url=HttpUrl("https://example.org/hp.owl"),
        namespace_prefix="HP",
        iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/HP_"),
        version="2024-04-26",
    )

    dataset = DatasetModel(**{**base_dataset_kwargs, "resources": [resource]})

    assert len(dataset.resources) == 1
    assert dataset.resources[0].id == "hp"
    assert dataset.resources[0].version == "2024-04-26"


def test_dataset_model_from_json():
    """Test loading DatasetModel from JSON file."""
    with open(FIXTURES_DIR / "dataset_minimal.json") as f:
        data = json.load(f)

    dataset = DatasetModel.model_validate(data)

    assert dataset.id == "dataset-json-001"
    assert dataset.title == "Test Dataset from JSON"
    assert len(dataset.keywords) == 2
    assert dataset.keywords[0] == "test"
    assert isinstance(dataset.keywords[1], OntologyClass)
    assert dataset.keywords[1].id == "HP:0001250"
