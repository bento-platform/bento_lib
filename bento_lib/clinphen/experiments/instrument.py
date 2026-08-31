from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_BLANKABLE, FIELD_NULLABLE
from .._models import BentoClinPhenModel


class Instrument(BentoClinPhenModel):
    identifier: str = FIELD_BLANKABLE
    device: str = FIELD_BLANKABLE
    device_ontology: OntologyClass | None = FIELD_NULLABLE
    description: str = FIELD_BLANKABLE
    extra_properties: dict  # TODO
