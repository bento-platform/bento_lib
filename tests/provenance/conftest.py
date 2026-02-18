"""Shared fixtures for provenance tests."""

import json
from pathlib import Path

import pytest

from bento_lib.provenance import DatasetModel, Person
from bento_lib.provenance.external.pcgl import Study


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def pcgl_study_full():
    with open(FIXTURES_DIR / "pcgl_study_full.json") as f:
        return Study.model_validate(json.load(f))


@pytest.fixture
def pcgl_study_minimal():
    with open(FIXTURES_DIR / "pcgl_study_minimal.json") as f:
        return Study.model_validate(json.load(f))


@pytest.fixture
def dataset_full():
    with open(FIXTURES_DIR / "dataset_full.json") as f:
        return DatasetModel.model_validate(json.load(f))


@pytest.fixture
def dataset_minimal():
    with open(FIXTURES_DIR / "dataset_minimal.json") as f:
        return DatasetModel.model_validate(json.load(f))

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
