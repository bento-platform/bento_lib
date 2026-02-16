from bento_lib.ontologies.models import OntologyClass
from bento_lib.provenance.dataset import Person, Organization, SpatialCoverageFeature, License, PublicationVenue, Phone, LongDescription
from bento_lib.i18n import FR


def test_dataset_model_full(dataset_full):
    """Test full DatasetModel validates and key nested types are correct."""
    ds = dataset_full

    assert ds.id == "dataset-json-full-001"
    assert ds.title == "Full Test Dataset from JSON"

    # Nested types resolved correctly
    assert isinstance(ds.long_description, LongDescription)
    assert isinstance(ds.keywords[2], OntologyClass)
    assert isinstance(ds.stakeholders[0], Person)
    assert isinstance(ds.stakeholders[0].affiliations[1], Organization)
    assert isinstance(ds.stakeholders[0].affiliations[1].contact.phone, Phone)
    assert isinstance(ds.spatial_coverage, SpatialCoverageFeature)
    assert isinstance(ds.license, License)
    assert isinstance(ds.publications[0].publication_venue, PublicationVenue)

    # Collection lengths as a smoke test for list parsing
    assert len(ds.keywords) == 4
    assert len(ds.stakeholders) == 2
    assert len(ds.funding_sources) == 2
    assert len(ds.counts) == 2
    assert len(ds.links) == 2
    assert len(ds.logos) == 2
    assert len(ds.participant_criteria) == 2


def test_dataset_model_minimal(dataset_minimal):
    """Test minimal DatasetModel with only required/few optional fields."""
    ds = dataset_minimal

    assert ds.id == "dataset-json-001"
    assert ds.title == "Test Dataset from JSON"
    assert isinstance(ds.keywords[1], OntologyClass)
    assert isinstance(ds.stakeholders[0], Person)
    assert ds.study_status == "ONGOING"


def test_dataset_model_translation(dataset_full):
    ds = dataset_full
    ds.language = FR

    assert ds.id == "dataset-json-full-001"
    assert ds.stakeholders[1].roles[0] == "Co-Investigator"
    assert ds.publications[0].publication_type == "Journal Article"
    assert ds.publications[0].publication_venue.venue_type == "Journal"

    # when serialized, serialized based on language
    ds_fr = ds.model_dump()

    assert ds_fr['id'] == "dataset-json-full-001"
    assert ds_fr['stakeholders'][1]['roles'][0] == "Co-chercheur"
    assert ds_fr['publications'][0]['publication_type'] == "Article de revue"
    assert ds_fr['publications'][0]['publication_venue']['venue_type'] == "Revue"

