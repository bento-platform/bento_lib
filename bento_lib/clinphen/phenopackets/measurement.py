from pydantic import Field

from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_BLANKABLE, FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .procedure import Procedure
from .quantity import Quantity
from .time_element import TimeElement

__all__ = [
    "TypedQuantity",
    "ComplexValue",
    "ValueQuantity",
    "ValueOntologyClass",
    "BaseMeasurement",
    "MeasurementWithValue",
    "MeasurementWithComplexValue",
    "Measurement",
]


class TypedQuantity(BentoClinPhenModel):
    type: OntologyClass
    quantity: Quantity


class ComplexValue(BentoClinPhenModel):
    typed_quantities: list[TypedQuantity] = Field(..., min_length=1)


class ValueQuantity(BentoClinPhenModel):
    quantity: Quantity | OntologyClass


class ValueOntologyClass(BentoClinPhenModel):
    ontology_class: OntologyClass


class BaseMeasurement(BentoClinPhenModel):
    description: str = FIELD_BLANKABLE
    assay: OntologyClass
    time_observed: TimeElement | None = FIELD_NULLABLE
    procedure: Procedure | None = FIELD_NULLABLE


class MeasurementWithValue(BaseMeasurement):
    value: ValueQuantity | ValueOntologyClass


class MeasurementWithComplexValue(BaseMeasurement):
    complex_value: ComplexValue = Field(..., alias="complexValue")


type Measurement = MeasurementWithValue | MeasurementWithComplexValue
