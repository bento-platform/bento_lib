from pydantic import BaseModel

from bento_lib.ontologies.models import OntologyClass
from .._fields import FIELD_BLANKABLE, FIELD_NULLABLE


class Instrument(BaseModel):
    identifier: str = FIELD_BLANKABLE
    device: str = FIELD_BLANKABLE
    device_ontology: OntologyClass | None = FIELD_NULLABLE
    description: str = FIELD_BLANKABLE
    extra_properties: dict  # TODO
