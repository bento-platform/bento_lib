"""Shared fixtures for provenance tests."""

import pytest
from datetime import date

from bento_lib.discovery.models.provenance import Contact, Organization, Person, DatasetModel


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
        grant_number=None,
    )


@pytest.fixture
def basic_funder(basic_contact):
    """Reusable funder organization."""
    return Organization(
        name="National Funder",
        description=None,
        contact=basic_contact,
        roles=["Funder"],
        grant_number="GRANT-123",
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
        "dataset_id": "test-study-001",
        "keywords": [],
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
        "pcgl_domain": ["Cancer"],
        "pcgl_status": "ONGOING",
        "pcgl_context": "RESEARCH",
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
