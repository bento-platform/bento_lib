"""Converter functions for transforming PCGL Study schema to DatasetModel."""

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
)
from ..external.pcgl import Study
from bento_lib.discovery.models.ontology import OntologyTerm


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
    keywords: list[str | OntologyTerm] = list(study.keywords)

    stakeholders: list[Person | Organization] = []
    stakeholders.extend(
        Person(
            name=pi.name,
            honorific=None,
            other_names=[],
            affiliations=[pi.affiliation] if pi.affiliation else [],
            roles=["Principal Investigator"],
        )
        for pi in study.principal_investigators
    )

    stakeholders.extend(
        Organization(
            name=org_name,
            description=None,
            contact=Contact(email=[], address=None, phone=None),
            roles=["Institution"],
            grant_number=None,
        )
        for org_name in study.lead_organizations
    )

    stakeholders.extend(
        Organization(
            name=c.name,
            description=None,
            contact=Contact(email=[], address=None, phone=None),
            roles=[cast(Role, c.role)] if c.role else [cast(Role, "Collaborating Organization")],
            grant_number=None,
        )
        for c in study.collaborators
    )

    stakeholders.extend(
        Organization(
            name=f.funder_name,
            description=None,
            contact=Contact(email=[], address=None, phone=None),
            roles=["Funder"],
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
        for url in study.publication_links
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
        pcgl_domain=list(study.domain),  # Convert list[StudyDomain] to list[str]
        pcgl_status=study.status,
        pcgl_context=study.context,
        pcgl_program_name=study.program_name,
    )


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
