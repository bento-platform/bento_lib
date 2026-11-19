"""
https://phenopacket-schema.readthedocs.io/en/latest/time-element.html
"""

from datetime import datetime

from bento_lib.ontologies.models import OntologyClass

from .._models import BentoClinPhenModel
from .age import Age, AgeRange, GestationalAge
from .time_interval import TimeInterval


class TimeElementOntologyClass(BentoClinPhenModel):
    ontology_class: OntologyClass


class TimeElementTimestamp(BentoClinPhenModel):
    timestamp: datetime  # TODO


class TimeElementInterval(BentoClinPhenModel):
    interval: TimeInterval


type TimeElement = (
    Age | AgeRange | GestationalAge | TimeElementOntologyClass | TimeElementTimestamp | TimeElementInterval
)
