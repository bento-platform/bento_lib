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
        first_name="Jane",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )


@pytest.fixture
def basic_institution(basic_contact):
    """Reusable institution."""
    return Organization(
        name="Test University",
        description=None,
        contact=basic_contact,
        role=["Institution"],
        grant_number=None,
    )


@pytest.fixture
def basic_funder(basic_contact):
    """Reusable funder organization."""
    return Organization(
        name="National Funder",
        description=None,
        contact=basic_contact,
        role=["Funder"],
        grant_number="GRANT-123",
    )


@pytest.fixture
def minimal_dataset(basic_pi, basic_institution, basic_funder):
    """Minimal valid dataset for testing conversions."""
    return DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test Description",
        keywords=[],
        stakeholders=[basic_pi, basic_institution, basic_funder],
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
        status="Ongoing",
        context="Research",
        program_name=None,
    )
