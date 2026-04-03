from operator import not_
from pydantic import BaseModel, Field
from typing import Literal

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none
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


class DoseInterval(BaseModel):
    quantity: Quantity
    schedule_frequency: OntologyClass
    interval: TimeInterval


class Treatment(BaseModel):
    agent: OntologyClass
    route_of_administration: OntologyClass | None
    dose_intervals: list[DoseInterval] = Field(default_factory=list, exclude_if=not_)
    drug_type: DrugType | None = Field(default=None, exclude_if=is_none)
    cumulative_dose: Quantity | None


class RadiationTherapy(BaseModel):
    modality: OntologyClass
    body_site: OntologyClass
    dosage: int
    fractions: int


class TherapeuticRegimen(BaseModel):
    identifier: OntologyClass | ExternalReference
    start_time: TimeElement | None
    end_time: TimeElement | None
    regimen_status: RegimenStatus


class MedicalAction(BaseModel):
    action: Procedure | Treatment | RadiationTherapy | TherapeuticRegimen
    treatment_target: OntologyClass | None
    treatment_intent: OntologyClass | None
    response_to_treatment: OntologyClass | None
    adverse_events: list[OntologyClass] = Field(default_factory=list, )
    treatment_termination_reason: OntologyClass | None
