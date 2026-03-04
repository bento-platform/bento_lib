"""Converter functions for transforming PCGL Study schema to DatasetModel."""

__all__ = ["pcgl_study_to_dataset"]

from collections import defaultdict
from datetime import date
from typing import cast
from ..dataset import (
    Count,
    DatasetModel,
    FundingSource,
    License,
    Link,
    Organization,
    ParticipantCriteria,
    Person,
    PersonOrOrganization,
    Publication,
    RoleAnnotated,
)
from ..external.pcgl import Study
from bento_lib.ontologies.models import OntologyClass


def _parse_participant_criteria(criteria_str: str | None) -> list[ParticipantCriteria] | None:
    """Parse PCGL participant criteria string into a list of ParticipantCriteria.

    Expected format: "Inclusion: description; Exclusion: description"
    """
    if not criteria_str:
        return None
    result = []
    for chunk in criteria_str.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ": " in chunk:
            criterion_type, description = chunk.split(": ", 1)
            result.append(ParticipantCriteria(type=criterion_type.strip(), description=description.strip()))
    return result or None


def pcgl_study_to_dataset(
    study: Study,
    release_date: date,
    last_modified: date,
    primary_contact: PersonOrOrganization,
    links: list[Link],
    counts: list[Count],
    spatial_coverage: str | None = None,
    version: str | None = None,
    privacy: str | None = None,
    license: License | None = None,
) -> DatasetModel:
    """Convert PCGL Study to DatasetModel. Requires additional metadata not in PCGL."""
    keywords: list[str | OntologyClass] = list(study.keywords)

    stakeholders: list[PersonOrOrganization] = []
    stakeholders.extend(
        Person(
            type="person",
            name=pi.name,
            honorific=None,
            other_names=None,
            affiliations=[pi.affiliation] if pi.affiliation else None,
            roles=["Principal Investigator"],
        )
        for pi in study.principal_investigators
    )

    stakeholders.extend(
        Organization(
            type="organization",
            name=org_name,
            description=None,
            contact=None,
            roles=["Institution"],
        )
        for org_name in study.lead_organizations
    )

    stakeholders.extend(
        Organization(
            type="organization",
            name=c.name,
            description=None,
            contact=None,
            roles=[cast(RoleAnnotated, c.role)] if c.role else [cast(RoleAnnotated, "Collaborating Organization")],
        )
        for c in study.collaborators
    )

    # Group funding sources by funder name to consolidate grant numbers
    funder_grants: defaultdict[str, list[str]] = defaultdict(list)
    for f in study.funding_sources:
        grants = funder_grants[f.funder_name]
        if f.grant_number:
            grants.append(f.grant_number)

    funding_sources = [
        FundingSource(funder=funder_name, grant_numbers=grant_numbers or None)
        for funder_name, grant_numbers in funder_grants.items()
    ] or None

    publications = [
        Publication(
            title=str(url),
            url=url,
            doi=str(url).replace("https://doi.org/", "") if str(url).startswith("https://doi.org/") else None,
            publication_type="Journal Article",
            authors=[primary_contact],
            publication_date=None,
            publication_venue=None,
            description=None,
        )
        for url in study.publication_links
    ] or None

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
        counts=counts,
        primary_contact=primary_contact,
        links=links,
        publications=publications,
        release_date=release_date,
        last_modified=last_modified,
        participant_criteria=_parse_participant_criteria(study.participant_criteria),
        study_status=study.status,
        study_context=study.context,
        pcgl_domain=list(study.domain),  # Convert list[StudyDomain] to list[str]
        pcgl_program_name=study.program_name,
        extra_properties=None,
    )
