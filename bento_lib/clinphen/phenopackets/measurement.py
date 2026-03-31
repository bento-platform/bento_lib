from pydantic import BaseModel, Field

from bento_lib.ontologies.models import OntologyClass
from bento_lib.utils.operators import is_none, eq_blank
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


class TypedQuantity(BaseModel):
    type: OntologyClass
    quantity: Quantity


class ComplexValue(BaseModel):
    typed_quantities: list[TypedQuantity] = Field(..., min_length=1)


class ValueQuantity(BaseModel):
    quantity: Quantity | OntologyClass


class ValueOntologyClass(BaseModel):
    ontology_class: OntologyClass = Field(..., alias="ontologyClass")


class BaseMeasurement(BaseModel):
    description: str = Field(default="", exclude_if=eq_blank)
    assay: OntologyClass
    time_observed: TimeElement | None = Field(alias="timeObserved", default=None, exclude_if=is_none)
    procedure: Procedure | None = Field(default=None, exclude_if=is_none)


class MeasurementWithValue(BaseMeasurement):
    value: ValueQuantity | ValueOntologyClass


class MeasurementWithComplexValue(BaseMeasurement):
    complex_value: ComplexValue = Field(..., alias="complexValue")


type Measurement = MeasurementWithValue | MeasurementWithComplexValue
