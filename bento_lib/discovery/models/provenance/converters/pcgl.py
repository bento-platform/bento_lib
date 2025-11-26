"""Converter functions for transforming between DatasetModel and PCGL Study schema."""

from datetime import date
from typing import cast
from pydantic import HttpUrl

from ..dataset import (
    DatasetModel,
    Organization,
    Person,
    Other,
    Contact,
    ParticipantCriteria,
    Publication,
    Role,
    StudyDomain,
)
from ..external.pcgl import Study, PrincipalInvestigator, Collaborator, FundingSource, StudyDomain as PCGLStudyDomain
from bento_lib.discovery.models.ontology import OntologyTerm


def dataset_to_pcgl_study(dataset: DatasetModel, study_id: str, dac_id: str) -> Study:
    """Convert DatasetModel to PCGL Study. Requires study_id and dac_id (not in DatasetModel)."""
    keywords = [kw.label if isinstance(kw, OntologyTerm) else kw for kw in dataset.keywords]
    domains: list[PCGLStudyDomain] = ["Other" if isinstance(d, Other) else d for d in dataset.domain]

    principal_investigators = _extract_principal_investigators(dataset.stakeholders)
    if not principal_investigators:
        raise ValueError("No principal investigators found. At least one required.")

    lead_organizations = _extract_lead_organizations(dataset.stakeholders)
    if not lead_organizations:
        raise ValueError("No lead organizations found. At least one required.")

    funding_sources = _extract_funding_sources(dataset.stakeholders)
    if not funding_sources:
        raise ValueError("No funding sources found. At least one required.")

    return Study(
        studyId=study_id,
        studyName=dataset.title,
        studyDescription=dataset.description,
        programName=dataset.program_name,
        keywords=keywords or None,
        status=dataset.status,
        context=dataset.context,
        domain=domains,
        dacId=dac_id,
        participantCriteria=_convert_participant_criteria(dataset.participant_criteria),
        principalInvestigators=principal_investigators,
        leadOrganizations=lead_organizations,
        collaborators=_extract_collaborators(dataset.stakeholders) or None,
        fundingSources=funding_sources,
        publicationLinks=_extract_doi_publication_links(dataset.publications) or None,
    )


def pcgl_study_to_dataset(
    study: Study,
    release_date: date,
    last_modified: date,
    primary_contact: Person | Organization,
    data_access_links: list[HttpUrl] | None = None,
    spatial_coverage: str | None = None,
    version: str | None = None,
    privacy: str | None = None,
    license=None,
    counts: list | None = None,
) -> DatasetModel:
    """Convert PCGL Study to DatasetModel. Requires additional metadata not in PCGL."""
    keywords: list[str | OntologyTerm] = list(study.keywords or [])
    domains: list[StudyDomain | Other] = [
        cast(StudyDomain, d) if d != "Other" else Other(other=d) for d in study.domain
    ]

    stakeholders: list[Person | Organization] = []
    stakeholders.extend(
        Person(
            first_name=pi.first_name,
            last_name=pi.last_name,
            honorific=None,
            other_names=[],
            affiliations=[pi.affiliation] if pi.affiliation else [],
            role=["Principal Investigator"],
        )
        for pi in study.principal_investigators
    )

    stakeholders.extend(
        Organization(
            name=org_name,
            description=None,
            contact=Contact(email=[], address=None, phone=None),
            role=["Institution"],
            grant_number=None,
        )
        for org_name in study.lead_organizations
    )

    if study.collaborators:
        stakeholders.extend(
            Organization(
                name=c.name,
                description=None,
                contact=Contact(email=[], address=None, phone=None),
                role=[cast(Role, c.role)] if c.role else [cast(Role, "Collaborating Organization")],
                grant_number=None,
            )
            for c in study.collaborators
        )

    stakeholders.extend(
        Organization(
            name=f.funder_name,
            description=None,
            contact=Contact(email=[], address=None, phone=None),
            role=["Funder"],
            grant_number=f.grant_number,
        )
        for f in study.funding_sources
    )

    publications = [
        Publication(
            title="",
            url=url,
            doi=str(url).replace("https://doi.org/", "") if str(url).startswith("https://doi.org/") else None,
            publication_type=Other(other="Journal Article"),
            authors=None,
            publication_date=None,
            journal=None,
            description=None,
        )
        for url in (study.publication_links or [])
    ]

    return DatasetModel(
        schema_version="1.0",
        title=study.study_name,
        description=study.study_description,
        keywords=keywords,
        stakeholders=stakeholders,
        spatial_coverage=spatial_coverage,
        version=version,
        privacy=privacy,
        license=license,
        counts=counts or [],
        primary_contact=primary_contact,
        publications=publications,
        data_access_links=data_access_links or [],
        release_date=release_date,
        last_modified=last_modified,
        participant_criteria=_parse_participant_criteria(study.participant_criteria),
        domain=domains,
        status=study.status,
        context=study.context,
        program_name=study.program_name,
    )


def _extract_principal_investigators(stakeholders: list[Organization | Person]) -> list[PrincipalInvestigator]:
    pis = []
    for s in stakeholders:
        if isinstance(s, Person) and "Principal Investigator" in s.role:
            affiliation = ""
            if s.affiliations:
                aff = s.affiliations[0]
                affiliation = aff.name if isinstance(aff, Organization) else aff
            pis.append(PrincipalInvestigator(first_name=s.first_name, last_name=s.last_name, affiliation=affiliation))
    return pis


def _extract_lead_organizations(stakeholders: list[Organization | Person]) -> list[str]:
    leadership_roles = {"Principal Investigator", "Sponsoring Organization", "Institution", "Research Center", "Site"}
    return [s.name for s in stakeholders if isinstance(s, Organization) and any(r in leadership_roles for r in s.role)]


def _extract_collaborators(stakeholders: list[Organization | Person]) -> list[Collaborator]:
    excluded = {"Principal Investigator", "Funder", "Sponsor", "Grant Agency"}
    leadership = {"Sponsoring Organization", "Institution", "Research Center", "Site"}
    collaborators = []

    for s in stakeholders:
        relevant = [r for r in s.role if r not in excluded]
        if not relevant:
            continue

        if isinstance(s, Person):
            collaborators.append(Collaborator(name=f"{s.first_name} {s.last_name}", role=relevant[0]))
        elif isinstance(s, Organization) and not any(r in leadership for r in s.role):
            collaborators.append(Collaborator(name=s.name, role=relevant[0]))

    return collaborators


def _extract_funding_sources(stakeholders: list[Organization | Person]) -> list[FundingSource]:
    funding_roles = {"Funder", "Sponsor", "Grant Agency"}
    funding = []

    for s in stakeholders:
        if any(r in funding_roles for r in s.role):
            if isinstance(s, Organization):
                funding.append(FundingSource(funder_name=s.name, grant_number=s.grant_number))
            elif isinstance(s, Person):
                funding.append(FundingSource(funder_name=f"{s.first_name} {s.last_name}", grant_number=None))

    return funding


def _extract_doi_publication_links(publications: list) -> list[HttpUrl]:
    return [p.url for p in publications if str(p.url).startswith("https://doi.org/")]


def _convert_participant_criteria(criteria_list: list) -> str | None:
    return "; ".join(f"{c.type}: {c.description}" for c in criteria_list) if criteria_list else None


def _parse_participant_criteria(criteria_str: str | None) -> list[ParticipantCriteria]:
    if not criteria_str:
        return []

    criteria_list = []
    for part in criteria_str.split("; "):
        if ": " in part:
            type_str, description = part.split(": ", 1)
            if type_str == "Inclusion":
                criteria_list.append(ParticipantCriteria(type="Inclusion", description=description))
            elif type_str == "Exclusion":
                criteria_list.append(ParticipantCriteria(type="Exclusion", description=description))

    return criteria_list
