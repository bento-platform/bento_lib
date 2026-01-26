"""Shared fixtures for provenance tests."""

import json
from pathlib import Path

import pytest
from datetime import date

from bento_lib.provenance import Contact, Organization, Person, DatasetModel
from bento_lib.provenance.external.pcgl import Study


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def basic_contact():
    """Reusable empty contact."""
    return Contact(email=[], address=None, phone=None)


@pytest.fixture
def basic_pi():
    """Reusable principal investigator."""
    return Person(
        name="Jane Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        roles=["Principal Investigator"],
    )


@pytest.fixture
def basic_institution(basic_contact):
    """Reusable institution."""
    return Organization(
        name="Test University",
        description=None,
        contact=basic_contact,
        roles=["Institution"],
    )


@pytest.fixture
def basic_funder(basic_contact):
    """Reusable funder organization."""
    return Organization(
        name="National Funder",
        description=None,
        contact=basic_contact,
        roles=["Funder"],
    )


@pytest.fixture
def base_dataset_kwargs(basic_pi):
    """Base kwargs dict for DatasetModel with sensible defaults.

    Use with dictionary expansion to override specific fields:
        dataset = DatasetModel(**{**base_dataset_kwargs, "title": "Custom Title"})
    """
    return {
        "schema_version": "1.0",
        "title": "Test Study",
        "description": "Test",
        "id": "test-study-001",
        "keywords": [],
        "resources": [],
        "stakeholders": [basic_pi],
        "spatial_coverage": None,
        "version": None,
        "privacy": None,
        "license": None,
        "counts": [],
        "primary_contact": basic_pi,
        "links": [],
        "publications": [],
        "data_access_links": [],
        "release_date": date(2023, 1, 1),
        "last_modified": date(2023, 1, 1),
        "participant_criteria": [],
        "study_status": "ONGOING",
        "study_context": "RESEARCH",
        "pcgl_domain": ["Cancer"],
        "pcgl_program_name": None,
    }


@pytest.fixture
def minimal_dataset(base_dataset_kwargs, basic_institution, basic_funder):
    """Minimal valid dataset for testing conversions."""
    return DatasetModel(
        **{
            **base_dataset_kwargs,
            "stakeholders": [
                base_dataset_kwargs["primary_contact"],
                basic_institution,
                basic_funder,
            ],
        }
    )


@pytest.fixture
def pcgl_study_full():
    """Full PCGL Study loaded from JSON fixture."""
    with open(FIXTURES_DIR / "pcgl_study_full.json") as f:
        return Study.model_validate(json.load(f))


@pytest.fixture
def pcgl_study_minimal():
    """Minimal PCGL Study loaded from JSON fixture."""
    with open(FIXTURES_DIR / "pcgl_study_minimal.json") as f:
        return Study.model_validate(json.load(f))
