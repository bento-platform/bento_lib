import pytest
from datetime import date
from pydantic import HttpUrl, ValidationError

from bento_lib.discovery.models.ontology import OntologyTerm
from bento_lib.discovery.models.provenance import (
    DatasetModel,
    Contact,
    Count,
    License,
    Organization,
    ParticipantCriteria,
    Person,
    Phone,
    Publication,
    Other,
)
from bento_lib.discovery.models.provenance.external.pcgl import (
    Study,
    PrincipalInvestigator,
    Collaborator,
    FundingSource,
)
from bento_lib.discovery.models.provenance.converters.pcgl import (
    dataset_to_pcgl_study,
    pcgl_study_to_dataset,
)


# =============================================================================
# Test OntologyTerm
# =============================================================================


def test_ontology_term():
    """Test OntologyTerm model creation."""
    term = OntologyTerm(id="HP:0001250", label="Seizure")
    assert term.id == "HP:0001250"
    assert term.label == "Seizure"


# =============================================================================
# Test DatasetModel and related models
# =============================================================================


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
        role=["Institution"],
        grant_number="12345",
    )
    assert org.name == "Test University"
    assert "Institution" in org.role
    assert org.grant_number == "12345"


def test_person():
    """Test Person model."""
    person = Person(
        first_name="John",
        last_name="Doe",
        honorific="Dr.",
        other_names=["Johnny"],
        affiliations=["Test University"],
        role=["Principal Investigator"],
    )
    assert person.first_name == "John"
    assert person.last_name == "Doe"
    assert person.honorific == "Dr."
    assert "Principal Investigator" in person.role


def test_person_with_organization_affiliation():
    """Test Person with Organization affiliation."""
    org = Organization(
        name="Test University",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )
    person = Person(
        first_name="Jane",
        last_name="Smith",
        honorific=None,
        other_names=[],
        affiliations=[org, "Another University"],
        role=["Researcher"],
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
    pub = Publication(
        title="Test Study Results",
        url=HttpUrl("https://doi.org/10.1234/test"),
        doi="10.1234/test",
        publication_type="Journal Article",
        authors=["Smith J", "Doe J"],
        publication_date=date(2023, 1, 15),
        journal="Nature",
        description="Study description",
    )
    assert pub.title == "Test Study Results"
    assert pub.doi == "10.1234/test"
    assert len(pub.authors) == 2


def test_publication_with_other_type():
    """Test Publication with Other type."""
    pub = Publication(
        title="Conference Presentation",
        url=HttpUrl("https://example.com/presentation"),
        doi=None,
        publication_type=Other(other="Poster Presentation"),
        authors=None,
        publication_date=None,
        journal=None,
        description=None,
    )
    assert isinstance(pub.publication_type, Other)
    assert pub.publication_type.other == "Poster Presentation"


def test_dataset_model():
    """Test complete DatasetModel."""
    primary_contact = Person(
        first_name="John",
        last_name="Doe",
        honorific="Dr.",
        other_names=[],
        affiliations=["Test University"],
        role=["Principal Investigator"],
    )

    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific="Dr.",
        other_names=[],
        affiliations=["Test University"],
        role=["Principal Investigator"],
    )

    institution = Organization(
        name="Test University",
        description="Research institution",
        contact=Contact(email=["contact@test.edu"], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="National Science Foundation",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number="NSF-12345",
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="A comprehensive test study",
        keywords=["genomics", "cancer"],
        stakeholders=[pi, institution, funder],
        spatial_coverage="Canada",
        version="1.0",
        privacy="Controlled Access",
        license=License(
            label="CC BY 4.0", type="Creative Commons", url=HttpUrl("https://creativecommons.org/licenses/by/4.0/")
        ),
        counts=[Count(count_entity="participants", value=100, description="Total participants")],
        primary_contact=primary_contact,
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


def test_dataset_model_with_other_domain():
    """Test DatasetModel with Other domain."""
    primary_contact = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        keywords=[],
        stakeholders=[pi],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=primary_contact,
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


def test_dataset_model_with_ontology_keywords():
    """Test DatasetModel with OntologyTerm keywords."""
    primary_contact = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Test Study",
        description="Test",
        keywords=[
            "plain keyword",
            OntologyTerm(id="HP:0001250", label="Seizure"),
            OntologyTerm(id="MONDO:0005015", label="Diabetes mellitus"),
        ],
        stakeholders=[pi],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=primary_contact,
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


def test_dataset_model_validation_domain_required():
    """Test that domain is required and must have at least one item."""
    primary_contact = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    with pytest.raises(ValidationError) as exc:
        DatasetModel(
            schema_version="1.0",
            title="Test Study",
            description="Test",
            keywords=[],
            stakeholders=[primary_contact],
            spatial_coverage=None,
            version=None,
            privacy=None,
            license=None,
            counts=[],
            primary_contact=primary_contact,
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


# =============================================================================
# Test PCGL Study Model
# =============================================================================


def test_principal_investigator():
    """Test PrincipalInvestigator model."""
    pi = PrincipalInvestigator(first_name="John", last_name="Doe", affiliation="Test University")
    assert pi.first_name == "John"
    assert pi.last_name == "Doe"
    assert pi.affiliation == "Test University"


def test_collaborator():
    """Test Collaborator model."""
    collab = Collaborator(name="Partner Organization", role="Data Contributor")
    assert collab.name == "Partner Organization"
    assert collab.role == "Data Contributor"

    collab_no_role = Collaborator(name="Another Partner", role=None)
    assert collab_no_role.role is None


def test_funding_source():
    """Test FundingSource model."""
    funding = FundingSource(funder_name="NIH", grant_number="R01-123456")
    assert funding.funder_name == "NIH"
    assert funding.grant_number == "R01-123456"

    funding_no_grant = FundingSource(funder_name="NSF", grant_number=None)
    assert funding_no_grant.grant_number is None


def test_pcgl_study():
    """Test complete PCGL Study model."""
    study = Study(
        studyId="STUDY001",
        studyName="Cancer Genomics Study",
        studyDescription="A comprehensive study of cancer genomics",
        programName="National Cancer Program",
        keywords=["cancer", "genomics", "precision medicine"],
        status="Ongoing",
        context="Research",
        domain=["Cancer", "Population Genomics"],
        dacId="DAC001",
        participantCriteria="Inclusion: Adults 18+; Exclusion: Pregnant individuals",
        principalInvestigators=[
            PrincipalInvestigator(first_name="Jane", last_name="Smith", affiliation="Test University")
        ],
        leadOrganizations=["Test University", "Research Hospital"],
        collaborators=[Collaborator(name="Partner Lab", role="Data Contributor")],
        fundingSources=[FundingSource(funder_name="NIH", grant_number="R01-123456")],
        publicationLinks=[HttpUrl("https://doi.org/10.1234/example")],
    )

    assert study.study_id == "STUDY001"
    assert study.study_name == "Cancer Genomics Study"
    assert len(study.keywords) == 3
    assert len(study.principal_investigators) == 1
    assert len(study.lead_organizations) == 2
    assert study.dac_id == "DAC001"


def test_pcgl_study_minimal():
    """Test PCGL Study with minimal required fields."""
    study = Study(
        studyId="STUDY002",
        studyName="Minimal Study",
        studyDescription="Description",
        programName=None,
        keywords=None,
        status="Completed",
        context="Clinical",
        domain=["Other"],
        dacId="DAC002",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(first_name="John", last_name="Doe", affiliation="Org")],
        leadOrganizations=["Organization"],
        collaborators=None,
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=None,
    )

    assert study.keywords is None
    assert study.collaborators is None
    assert study.publication_links is None


def test_pcgl_study_validation_doi_links():
    """Test that publicationLinks must be DOI URLs."""
    with pytest.raises(ValidationError) as exc:
        Study(
            studyId="STUDY003",
            studyName="Test Study",
            studyDescription="Description",
            programName=None,
            keywords=None,
            status="Ongoing",
            context="Research",
            domain=["Cancer"],
            dacId="DAC003",
            participantCriteria=None,
            principalInvestigators=[PrincipalInvestigator(first_name="John", last_name="Doe", affiliation="Org")],
            leadOrganizations=["Org"],
            collaborators=None,
            fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
            publicationLinks=[HttpUrl("https://example.com/paper")],  # Not a DOI URL
        )
    assert "must be a DOI URL" in str(exc.value)


def test_pcgl_study_validation_empty_lists():
    """Test that required lists cannot be empty."""
    # Empty principalInvestigators
    with pytest.raises(ValidationError) as exc:
        Study(
            studyId="STUDY004",
            studyName="Test Study",
            studyDescription="Description",
            programName=None,
            keywords=None,
            status="Ongoing",
            context="Research",
            domain=["Cancer"],
            dacId="DAC004",
            participalCriteria=None,
            principalInvestigators=[],  # Empty list
            leadOrganizations=["Org"],
            collaborators=None,
            fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
            publicationLinks=None,
        )
    assert "at least 1 item" in str(exc.value).lower()


# =============================================================================
# Test Converters
# =============================================================================


def test_dataset_to_pcgl_study():
    """Test converting DatasetModel to PCGL Study."""
    pi = Person(
        first_name="Jane",
        last_name="Smith",
        honorific="Dr.",
        other_names=[],
        affiliations=["Test University"],
        role=["Principal Investigator"],
    )

    institution = Organization(
        name="Test University",
        description="Research institution",
        contact=Contact(email=["contact@test.edu"], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="NIH",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number="R01-123456",
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Cancer Study",
        description="A cancer genomics study",
        keywords=["cancer", "genomics"],
        stakeholders=[pi, institution, funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=pi,
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
            ParticipantCriteria(type="Exclusion", description="Pregnant individuals"),
        ],
        domain=["Cancer"],
        status="Ongoing",
        context="Research",
        program_name="Cancer Genomics Program",
    )

    study = dataset_to_pcgl_study(dataset, study_id="STUDY001", dac_id="DAC001")

    assert study.study_id == "STUDY001"
    assert study.study_name == "Cancer Study"
    assert study.study_description == "A cancer genomics study"
    assert study.program_name == "Cancer Genomics Program"
    assert study.keywords == ["cancer", "genomics"]
    assert study.status == "Ongoing"
    assert study.context == "Research"
    assert study.domain == ["Cancer"]
    assert study.dac_id == "DAC001"
    assert study.participant_criteria == "Inclusion: Adults 18+; Exclusion: Pregnant individuals"
    assert len(study.principal_investigators) == 1
    assert study.principal_investigators[0].first_name == "Jane"
    assert study.principal_investigators[0].last_name == "Smith"
    assert len(study.lead_organizations) == 1
    assert "Test University" in study.lead_organizations
    assert len(study.funding_sources) == 1
    assert study.funding_sources[0].funder_name == "NIH"
    assert study.funding_sources[0].grant_number == "R01-123456"
    assert len(study.publication_links) == 1
    assert str(study.publication_links[0]) == "https://doi.org/10.1234/test"


def test_dataset_to_pcgl_study_with_ontology_keywords():
    """Test conversion with OntologyTerm keywords (should extract labels)."""
    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    institution = Organization(
        name="Test Org",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="Funder",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number=None,
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[
            "plain keyword",
            OntologyTerm(id="HP:0001250", label="Seizure"),
        ],
        stakeholders=[pi, institution, funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=pi,
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

    study = dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert study.keywords == ["plain keyword", "Seizure"]


def test_dataset_to_pcgl_study_with_other_domain():
    """Test conversion with Other domain (should become 'Other' string)."""
    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    institution = Organization(
        name="Test Org",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="Funder",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number=None,
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[pi, institution, funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=pi,
        publications=[],
        data_access_links=[],
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        participant_criteria=[],
        domain=[Other(other="Custom Domain")],
        status="Completed",
        context="Clinical",
        program_name=None,
    )

    study = dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert study.domain == ["Other"]


def test_dataset_to_pcgl_study_missing_pi():
    """Test that conversion fails if no Principal Investigator found."""
    # Only has a researcher, not a PI
    researcher = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Researcher"],
    )

    institution = Organization(
        name="Test Org",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    funder = Organization(
        name="Funder",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number=None,
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[researcher, institution, funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=researcher,
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

    with pytest.raises(ValueError) as exc:
        dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert "No principal investigators found" in str(exc.value)


def test_dataset_to_pcgl_study_missing_organization():
    """Test that conversion fails if no lead organization found."""
    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    funder = Organization(
        name="Funder",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number=None,
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[pi, funder],  # No institution
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=pi,
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

    with pytest.raises(ValueError) as exc:
        dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert "No lead organizations found" in str(exc.value)


def test_dataset_to_pcgl_study_missing_funder():
    """Test that conversion fails if no funding source found."""
    pi = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    institution = Organization(
        name="Test Org",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    dataset = DatasetModel(
        schema_version="1.0",
        title="Study",
        description="Description",
        keywords=[],
        stakeholders=[pi, institution],  # No funder
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=pi,
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

    with pytest.raises(ValueError) as exc:
        dataset_to_pcgl_study(dataset, study_id="S001", dac_id="D001")
    assert "No funding sources found" in str(exc.value)


def test_pcgl_study_to_dataset():
    """Test converting PCGL Study to DatasetModel."""
    study = Study(
        studyId="STUDY001",
        studyName="Cancer Study",
        studyDescription="A cancer genomics study",
        programName="Cancer Program",
        keywords=["cancer", "genomics"],
        status="Ongoing",
        context="Research",
        domain=["Cancer", "Population Genomics"],
        dacId="DAC001",
        participantCriteria="Inclusion: Adults 18+; Exclusion: Pregnant individuals",
        principalInvestigators=[
            PrincipalInvestigator(first_name="Jane", last_name="Smith", affiliation="Test University")
        ],
        leadOrganizations=["Test University", "Research Hospital"],
        collaborators=[
            Collaborator(name="Partner Lab", role="Data Contributor"),
            Collaborator(name="Another Partner", role=None),
        ],
        fundingSources=[
            FundingSource(funder_name="NIH", grant_number="R01-123456"),
            FundingSource(funder_name="NSF", grant_number=None),
        ],
        publicationLinks=[
            HttpUrl("https://doi.org/10.1234/example"),
            HttpUrl("https://doi.org/10.5678/another"),
        ],
    )

    primary_contact = Person(
        first_name="Jane",
        last_name="Smith",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 6, 1),
        primary_contact=primary_contact,
    )

    assert dataset.title == "Cancer Study"
    assert dataset.description == "A cancer genomics study"
    assert dataset.program_name == "Cancer Program"
    assert dataset.keywords == ["cancer", "genomics"]
    assert dataset.status == "Ongoing"
    assert dataset.context == "Research"
    assert dataset.domain[0] == "Cancer"
    assert dataset.domain[1] == "Population Genomics"
    assert dataset.release_date == date(2023, 1, 1)
    assert dataset.last_modified == date(2023, 6, 1)

    # Check participant criteria parsing
    assert len(dataset.participant_criteria) == 2
    assert dataset.participant_criteria[0].type == "Inclusion"
    assert dataset.participant_criteria[0].description == "Adults 18+"
    assert dataset.participant_criteria[1].type == "Exclusion"
    assert dataset.participant_criteria[1].description == "Pregnant individuals"

    # Check stakeholders
    # Should have: 1 PI, 2 institutions, 2 collaborators, 2 funders = 7 total
    assert len(dataset.stakeholders) == 7

    # Find PI
    pis = [s for s in dataset.stakeholders if isinstance(s, Person) and "Principal Investigator" in s.role]
    assert len(pis) == 1
    assert pis[0].first_name == "Jane"
    assert pis[0].last_name == "Smith"

    # Find institutions
    institutions = [s for s in dataset.stakeholders if isinstance(s, Organization) and "Institution" in s.role]
    assert len(institutions) == 2
    assert {inst.name for inst in institutions} == {"Test University", "Research Hospital"}

    # Find funders
    funders = [s for s in dataset.stakeholders if isinstance(s, Organization) and "Funder" in s.role]
    assert len(funders) == 2
    funder_names = {f.name for f in funders}
    assert "NIH" in funder_names
    assert "NSF" in funder_names
    nih_funder = next(f for f in funders if f.name == "NIH")
    assert nih_funder.grant_number == "R01-123456"

    # Check publications
    assert len(dataset.publications) == 2
    assert str(dataset.publications[0].url) == "https://doi.org/10.1234/example"
    assert dataset.publications[0].doi == "10.1234/example"


def test_pcgl_study_to_dataset_with_other_domain():
    """Test conversion with 'Other' domain (should become Other type)."""
    study = Study(
        studyId="STUDY002",
        studyName="Other Study",
        studyDescription="Description",
        programName=None,
        keywords=None,
        status="Completed",
        context="Clinical",
        domain=["Other"],
        dacId="DAC002",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(first_name="John", last_name="Doe", affiliation="Org")],
        leadOrganizations=["Organization"],
        collaborators=None,
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=None,
    )

    primary_contact = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=primary_contact,
    )

    assert len(dataset.domain) == 1
    assert isinstance(dataset.domain[0], Other)
    assert dataset.domain[0].other == "Other"


def test_pcgl_study_to_dataset_no_criteria():
    """Test conversion with no participant criteria."""
    study = Study(
        studyId="STUDY003",
        studyName="Study",
        studyDescription="Description",
        programName=None,
        keywords=None,
        status="Ongoing",
        context="Research",
        domain=["Cancer"],
        dacId="DAC003",
        participantCriteria=None,
        principalInvestigators=[PrincipalInvestigator(first_name="John", last_name="Doe", affiliation="Org")],
        leadOrganizations=["Organization"],
        collaborators=None,
        fundingSources=[FundingSource(funder_name="Funder", grant_number=None)],
        publicationLinks=None,
    )

    primary_contact = Person(
        first_name="John",
        last_name="Doe",
        honorific=None,
        other_names=[],
        affiliations=[],
        role=["Principal Investigator"],
    )

    dataset = pcgl_study_to_dataset(
        study=study,
        release_date=date(2023, 1, 1),
        last_modified=date(2023, 1, 1),
        primary_contact=primary_contact,
    )

    assert dataset.participant_criteria == []


def test_roundtrip_conversion():
    """Test converting Dataset -> Study -> Dataset maintains core information."""
    original_pi = Person(
        first_name="Jane",
        last_name="Smith",
        honorific="Dr.",
        other_names=[],
        affiliations=["Test University"],
        role=["Principal Investigator"],
    )

    original_institution = Organization(
        name="Test University",
        description="Research institution",
        contact=Contact(email=["contact@test.edu"], address=None, phone=None),
        role=["Institution"],
        grant_number=None,
    )

    original_funder = Organization(
        name="NIH",
        description=None,
        contact=Contact(email=[], address=None, phone=None),
        role=["Funder"],
        grant_number="R01-123456",
    )

    original_dataset = DatasetModel(
        schema_version="1.0",
        title="Cancer Study",
        description="A cancer genomics study",
        keywords=["cancer", "genomics"],
        stakeholders=[original_pi, original_institution, original_funder],
        spatial_coverage=None,
        version=None,
        privacy=None,
        license=None,
        counts=[],
        primary_contact=original_pi,
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
        primary_contact=original_pi,
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
