"""Converter functions for transforming PCGL Study schema to DatasetModel."""

__all__ = ["pcgl_study_to_dataset"]

from datetime import date
from typing import cast
from pydantic import HttpUrl

from ..dataset import (
    DatasetModel,
    FundingSource,
    License,
    Organization,
    Person,
    Other,
    Contact,
    ParticipantCriteria,
    Publication,
    Role,
)
from ..external.pcgl import Study
from bento_lib.ontologies.models import OntologyClass


def pcgl_study_to_dataset(
    study: Study,
    release_date: date,
    last_modified: date,
    primary_contact: Person | Organization,
    data_access_links: list[HttpUrl] | None = None,
    spatial_coverage: str | None = None,
    version: str | None = None,
    privacy: str | None = None,
    license: License | None = None,
    counts: list | None = None,
) -> DatasetModel:
    """Convert PCGL Study to DatasetModel. Requires additional metadata not in PCGL."""
    keywords: list[str | OntologyClass] = list(study.keywords)

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
        )
        for org_name in study.lead_organizations
    )

    stakeholders.extend(
        Organization(
            name=c.name,
            description=None,
            contact=Contact(email=[], address=None, phone=None),
            roles=[cast(Role, c.role)] if c.role else [cast(Role, "Collaborating Organization")],
        )
        for c in study.collaborators
    )

    # Group funding sources by funder name to consolidate grant numbers
    funder_grants: dict[str, list[str]] = {}
    for f in study.funding_sources:
        if f.funder_name not in funder_grants:
            funder_grants[f.funder_name] = []
        if f.grant_number:
            funder_grants[f.funder_name].append(f.grant_number)

    funding_sources = [
        FundingSource(funder=funder_name, grant_numbers=grant_numbers)
        for funder_name, grant_numbers in funder_grants.items()
    ]

    publications = [
        Publication(
            title="",
            url=url,
            doi=str(url).replace("https://doi.org/", "") if str(url).startswith("https://doi.org/") else None,
            publication_type=Other(other="Journal Article"),
            authors=[],
            publication_date=None,
            publication_venue=None,
            description=None,
        )
        for url in study.publication_links
    ]

    return DatasetModel(
        schema_version="1.0",
        title=study.study_name,
        description=study.study_description,
        id=study.study_id,
        keywords=keywords,
        stakeholders=stakeholders,
        funding_sources=funding_sources,
        spatial_coverage=spatial_coverage,
        version=version,
        privacy=privacy,
        license=license,
        counts=counts or [],
        primary_contact=primary_contact,
        links=[],
        publications=publications,
        data_access_links=data_access_links or [],
        release_date=release_date,
        last_modified=last_modified,
        participant_criteria=_parse_participant_criteria(study.participant_criteria),
        study_status=study.status,
        study_context=study.context,
        pcgl_domain=list(study.domain),  # Convert list[StudyDomain] to list[str]
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
