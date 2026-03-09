import pytest
from pydantic import ValidationError
from bento_lib.ontologies.models import OntologyClass
from bento_lib.provenance.dataset import (
    Contact,
    DatasetModelBase,
    DatasetModel,
    ProjectScopedDatasetModel,
    Person,
    Organization,
    License,
    PublicationVenue,
    Phone,
    LongDescription,
)
from bento_lib.i18n import FR


def test_dataset_model_full(dataset_full):
    """Test full DatasetModel validates and key nested types are correct."""
    ds = dataset_full

    assert ds.identifier == "dataset-json-full-001"
    assert ds.title == "Full Test Dataset from JSON"

    # Nested types resolved correctly
    assert isinstance(ds.long_description, LongDescription)
    assert isinstance(ds.keywords[2], OntologyClass)
    assert isinstance(ds.stakeholders[0], Person)
    assert isinstance(ds.stakeholders[0].affiliations[1], Organization)
    assert isinstance(ds.stakeholders[0].affiliations[1].contact.phone, Phone)
    assert str(ds.stakeholders[0].affiliations[1].contact.website) == "https://research.org/"
    assert isinstance(ds.spatial_coverage, str)
    assert isinstance(ds.license, License)
    assert isinstance(ds.publications[0].publication_venue, PublicationVenue)

    # Collection lengths as a smoke test for list parsing
    assert len(ds.keywords) == 4
    assert len(ds.stakeholders) == 2
    assert len(ds.funding_sources) == 2
    assert len(ds.counts) == 2
    assert len(ds.links) == 4
    assert len(ds.logos) == 2
    assert len(ds.participant_criteria) == 2


def test_dataset_model_minimal(dataset_minimal):
    """Test minimal DatasetModel with only required/few optional fields."""
    ds = dataset_minimal

    assert ds.identifier == "dataset-json-001"
    assert ds.title == "Test Dataset from JSON"
    assert ds.keywords is None
    assert ds.counts is None
    assert ds.participant_criteria is None
    assert ds.release_date is None
    assert ds.last_modified is None
    assert ds.pcgl_domain is None
    assert isinstance(ds.stakeholders[0], Person)
    assert ds.study_status == "ONGOING"


def test_dataset_model_translation(dataset_full):
    ds = dataset_full
    ds.language = FR

    assert ds.identifier == "dataset-json-full-001"
    assert ds.stakeholders[1].roles[0] == "Co-Investigator"
    assert ds.publications[0].publication_type == "Journal Article"
    assert ds.publications[0].publication_venue.venue_type == "Journal"

    # when serialized, serialized based on language
    ds_fr = ds.model_dump()

    assert ds_fr["identifier"] == "dataset-json-full-001"
    assert ds_fr["stakeholders"][1]["roles"][0] == "Co-chercheur"
    assert ds_fr["publications"][0]["publication_type"] == "Article de revue"
    assert ds_fr["publications"][0]["publication_venue"]["venue_type"] == "Revue"


def test_dataset_model_from_base(dataset_full):
    ds_dict = dataset_full.model_dump()
    del ds_dict["identifier"]
    dmb = DatasetModelBase.model_validate(ds_dict)
    ds = DatasetModel.from_base(dmb, "Dataset-001")

    assert ds.identifier == "Dataset-001"

    assert isinstance(ds, DatasetModel)

    assert isinstance(ds.long_description, LongDescription)
    assert isinstance(ds.keywords[2], OntologyClass)
    assert isinstance(ds.stakeholders[0], Person)
    assert isinstance(ds.stakeholders[0].affiliations[1], Organization)
    assert isinstance(ds.stakeholders[0].affiliations[1].contact.phone, Phone)
    assert isinstance(ds.spatial_coverage, str)
    assert isinstance(ds.license, License)
    assert isinstance(ds.publications[0].publication_venue, PublicationVenue)


def test_project_scoped_dataset_model_from_base(dataset_minimal):
    """from_base and from_dataset_model both create a valid ProjectScopedDatasetModel."""
    from uuid import UUID

    project_id = UUID("12345678-1234-5678-1234-567812345678")

    ds_dict = dataset_minimal.model_dump()
    del ds_dict["identifier"]
    base = DatasetModelBase.model_validate(ds_dict)
    ds = ProjectScopedDatasetModel.from_base(base, "dataset-002", project_id)
    assert ds.identifier == "dataset-002"
    assert ds.project == project_id
    assert isinstance(ds, ProjectScopedDatasetModel)

    ds2 = ProjectScopedDatasetModel.from_dataset_model(dataset_minimal, project_id)
    assert ds2.identifier == dataset_minimal.identifier
    assert ds2.project == project_id
    assert isinstance(ds2, ProjectScopedDatasetModel)


def test_contact_at_least_one_field():
    """Contact requires at least one field; email is now optional."""
    # valid: each field alone is sufficient
    assert Contact(website="https://example.com").website is not None
    assert Contact(email=["user@example.com"]).email == ["user@example.com"]
    assert Contact(address="123 Main St").address == "123 Main St"
    assert Contact(phone=Phone(country_code=1, number=5550000)).phone is not None

    # valid: email omitted entirely
    assert Contact(website="https://example.com", address="123 Main St").email is None

    # invalid: all fields omitted
    with pytest.raises(ValidationError, match="at least one field"):
        Contact()


def test_dataset_model_keyword_resource_validation(dataset_full):
    """OntologyClass keywords must have a matching resource by namespace_prefix."""
    ds_dict = dataset_full.model_dump()
    del ds_dict["identifier"]

    # Remove the HP resource — HP: CURIEs in keywords should now fail
    ds_dict["resources"] = None
    with pytest.raises(Exception, match="no matching resource"):
        DatasetModelBase.model_validate(ds_dict)

    # keywords=None should always pass regardless of resources
    ds_dict["keywords"] = None
    DatasetModelBase.model_validate(ds_dict)  # no error
