"""Tests for basic provenance models (DatasetModel, Contact, Person, Organization, etc.)."""

from datetime import date
from pydantic import HttpUrl
from geojson_pydantic import Point

from bento_lib.discovery.models.ontology import OntologyTerm
from bento_lib.discovery.models.provenance import (
    Contact,
    Count,
    License,
    Organization,
    ParticipantCriteria,
    Person,
    Phone,
    Publication,
    PublicationVenue,
    Other,
    SpatialCoverageFeature,
    SpatialCoverageProperties,
)


def test_ontology_term():
    """Test OntologyTerm model creation."""
    term = OntologyTerm(id="HP:0001250", label="Seizure")
    assert term.id == "HP:0001250"
    assert term.label == "Seizure"


def test_phone():
    """Test Phone model."""
    phone = Phone(country_code=1, number=5551234567, extension=None)
    assert phone.country_code == 1
    assert phone.number == 5551234567
    assert phone.extension is None

    phone_with_ext = Phone(country_code=1, number=5551234567, extension=123)
    assert phone_with_ext.extension == 123


def test_contact():
    """Test Contact model."""
    contact = Contact(
        email=["test@example.com", "test2@example.com"],
        address="123 Main St",
        phone=Phone(country_code=1, number=5551234567, extension=None),
    )
    assert len(contact.email) == 2
    assert contact.address == "123 Main St"
    assert contact.phone.number == 5551234567


def test_organization():
    """Test Organization model."""
    org = Organization(
        name="Test University",
        description="A research institution",
        contact=Contact(email=["contact@test.edu"], address=None, phone=None),
        roles=["Institution"],
        grant_number="12345",
    )
    assert org.name == "Test University"
    assert "Institution" in org.roles
    assert org.grant_number == "12345"


def test_person():
    """Test Person model."""
    person = Person(
        name="John Doe",
        honorific="Dr.",
        other_names=["Johnny"],
        affiliations=["Test University"],
        roles=["Principal Investigator"],
    )
    assert person.name == "John Doe"
    assert person.honorific == "Dr."
    assert "Principal Investigator" in person.roles


def test_person_with_organization_affiliation():
    """Test Person with Organization affiliation."""
    org = Organization(
        name="Test University",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        roles=["Institution"],
        grant_number=None,
    )
    person = Person(
        name="Jane Smith",
        honorific=None,
        other_names=[],
        affiliations=[org, "Another University"],
        roles=["Researcher"],
    )
    assert len(person.affiliations) == 2
    assert isinstance(person.affiliations[0], Organization)
    assert person.affiliations[1] == "Another University"


def test_participant_criteria():
    """Test ParticipantCriteria model."""
    inclusion = ParticipantCriteria(type="Inclusion", description="Adults 18 years and older")
    assert inclusion.type == "Inclusion"

    exclusion = ParticipantCriteria(type="Exclusion", description="Pregnant individuals")
    assert exclusion.type == "Exclusion"


def test_count():
    """Test Count model."""
    count = Count(count_entity="participants", value=100, description="Total number of participants")
    assert count.count_entity == "participants"
    assert count.value == 100


def test_license():
    """Test License model."""
    license = License(
        label="CC BY 4.0", type="Creative Commons", url=HttpUrl("https://creativecommons.org/licenses/by/4.0/")
    )
    assert license.label == "CC BY 4.0"
    assert str(license.url) == "https://creativecommons.org/licenses/by/4.0/"


def test_publication():
    """Test Publication model."""
    author1 = Person(
        name="Jane Smith",
        honorific="Dr.",
        other_names=[],
        affiliations=["Test University"],
        roles=["Researcher"],
    )
    author2 = Organization(
        name="Research Institute",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        roles=["Institution"],
        grant_number=None,
    )

    venue = PublicationVenue(
        name="Nature",
        venue_type="Journal",
        publisher="Nature Publishing Group",
        location=None,
    )

    pub = Publication(
        title="Test Study Results",
        url=HttpUrl("https://doi.org/10.1234/test"),
        doi="10.1234/test",
        publication_type="Journal Article",
        authors=[author1, author2],
        publication_date=date(2023, 1, 15),
        publication_venue=venue,
        description="Study description",
    )
    assert pub.title == "Test Study Results"
    assert pub.doi == "10.1234/test"
    assert len(pub.authors) == 2
    assert isinstance(pub.authors[0], Person)
    assert isinstance(pub.authors[1], Organization)
    assert pub.authors[0].name == "Jane Smith"
    assert pub.publication_venue.name == "Nature"
    assert pub.authors[1].name == "Research Institute"


def test_publication_with_other_type():
    """Test Publication with Other type."""
    pub = Publication(
        title="Conference Presentation",
        url=HttpUrl("https://example.com/presentation"),
        doi=None,
        publication_type=Other(other="Poster Presentation"),
        authors=None,
        publication_date=None,
        publication_venue=None,
        description=None,
    )
    assert isinstance(pub.publication_type, Other)
    assert pub.publication_type.other == "Poster Presentation"


def test_publication_with_mixed_authors(basic_contact):
    """Test Publication with both Person and Organization authors."""
    person_author = Person(
        name="John Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        roles=["Researcher"],
    )
    org_author = Organization(
        name="Collaborative Group",
        description="A research consortium",
        contact=basic_contact,
        roles=["Collaborating Organization"],
        grant_number=None,
    )

    venue = PublicationVenue(
        name="Science",
        venue_type="Journal",
        publisher=None,
        location=None,
    )

    pub = Publication(
        title="Collaborative Study",
        url=HttpUrl("https://doi.org/10.5678/collab"),
        doi="10.5678/collab",
        publication_type="Journal Article",
        authors=[person_author, org_author],
        publication_date=date(2024, 3, 15),
        publication_venue=venue,
        description="A collaborative research paper",
    )

    assert len(pub.authors) == 2
    assert isinstance(pub.authors[0], Person)
    assert isinstance(pub.authors[1], Organization)


def test_spatial_coverage_properties():
    """Test SpatialCoverageProperties with name field."""
    props = SpatialCoverageProperties(name="Canada")
    assert props.name == "Canada"

    # Test with extra fields (should be allowed)
    props_with_extra = SpatialCoverageProperties(name="Ontario", region="North America", population=14000000)
    assert props_with_extra.name == "Ontario"
    assert props_with_extra.model_extra["region"] == "North America"  # type: ignore


def test_spatial_coverage_feature():
    """Test SpatialCoverageFeature with GeoJSON."""
    feature = SpatialCoverageFeature(
        type="Feature",
        geometry=Point(type="Point", coordinates=[-79.3832, 43.6532]),
        properties=SpatialCoverageProperties(name="Toronto"),
    )
    assert feature.properties.name == "Toronto"
    assert feature.geometry.type == "Point"
    assert feature.geometry.coordinates.longitude == -79.3832
    assert feature.geometry.coordinates.latitude == 43.6532
