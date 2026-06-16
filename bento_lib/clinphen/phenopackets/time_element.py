from datetime import datetime
from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from .age import Age, AgeRange, GestationalAge
from .time_interval import TimeInterval


class TimeElementOntologyClass(BaseModel):
    ontology_class: OntologyClass = Field(..., alias="ontologyClass")


class TimeElementTimestamp(BaseModel):
    timestamp: datetime  # TODO


class TimeElementInterval(BaseModel):
    interval: TimeInterval


type TimeElement = (
    Age | AgeRange | GestationalAge | TimeElementOntologyClass | TimeElementTimestamp | TimeElementInterval
)
