"""Converter functions for transforming DatasetModel to PCGL Study schema."""

from pydantic import HttpUrl

from ..dataset import DatasetModel, Organization, Person, Other
from ..external.pcgl import Study, PrincipalInvestigator, Collaborator, FundingSource, StudyDomain as PCGLStudyDomain
from bento_lib.discovery.models.ontology import OntologyTerm


def dataset_to_pcgl_study(dataset: DatasetModel, study_id: str, dac_id: str) -> Study:
    """
    Convert DatasetModel to PCGL Study.

    Args:
        dataset: DatasetModel instance to convert
        study_id: Unique study identifier (not in DatasetModel)
        dac_id: Data Access Committee ID (not in DatasetModel)

    Raises:
        ValueError: If required PCGL fields cannot be derived
    """
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
