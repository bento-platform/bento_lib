from operator import not_
from typing import Literal

from pydantic import Field

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .external_reference import ExternalReference
from .procedure import Procedure
from .quantity import Quantity
from .time_element import TimeElement
from .time_interval import TimeInterval

__all__ = ["RegimenStatus", "Treatment", "RadiationTherapy", "TherapeuticRegimen", "MedicalAction"]


type DrugType = Literal[
    "UNKNOWN_DRUG_TYPE", "PRESCRIPTION", "EHR_MEDICATION_LIST", "ADMINISTRATION_RELATED_TO_PROCEDURE"
]

type RegimenStatus = Literal["UNKNOWN_STATUS", "STARTED", "COMPLETED", "DISCONTINUED"]


class DoseInterval(BentoClinPhenModel):
    quantity: Quantity
    schedule_frequency: OntologyClass
    interval: TimeInterval


class Treatment(BentoClinPhenModel):
    agent: OntologyClass
    route_of_administration: OntologyClass | None = FIELD_NULLABLE
    dose_intervals: list[DoseInterval] = Field(default_factory=list, exclude_if=not_)
    drug_type: DrugType | None = FIELD_NULLABLE
    cumulative_dose: Quantity | None = FIELD_NULLABLE


class RadiationTherapy(BentoClinPhenModel):
    modality: OntologyClass
    body_site: OntologyClass
    dosage: int
    fractions: int


class TherapeuticRegimen(BentoClinPhenModel):
    identifier: OntologyClass | ExternalReference
    start_time: TimeElement | None = FIELD_NULLABLE
    end_time: TimeElement | None = FIELD_NULLABLE
    regimen_status: RegimenStatus


class MedicalAction(BentoClinPhenModel):
    action: Procedure | Treatment | RadiationTherapy | TherapeuticRegimen
    treatment_target: OntologyClass | None = FIELD_NULLABLE
    treatment_intent: OntologyClass | None = FIELD_NULLABLE
    response_to_treatment: OntologyClass | None = FIELD_NULLABLE
    adverse_events: list[OntologyClass] = Field(default_factory=list)
    treatment_termination_reason: OntologyClass | None = FIELD_NULLABLE
