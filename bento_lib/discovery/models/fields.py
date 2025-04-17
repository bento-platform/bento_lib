from pydantic import AliasChoices, BaseModel, Field
from typing import Literal

__all__ = [
    "BaseFieldDefinition",
    # string
    "StringFieldConfig",
    "StringFieldDefinition",
    # number
    "BaseNumberFieldConfig",
    "ManualBinsNumberFieldConfig",
    "AutoBinsNumberFieldConfig",
    "NumberFieldDefinition",
    # date
    "DateFieldConfig",
    "DateFieldDefinition",
    # sum type:
    "FieldDefinition",
]


DataTypeField = Field(validation_alias=AliasChoices("data_type", "datatype"))


class BaseFieldDefinition(BaseModel):
    mapping: str
    title: str  # TODO: make optional and pull from Bento schema if not set
    description: str  # TODO: make optional and pull from Bento schema if not set
    data_type: Literal["string", "number", "date"] = DataTypeField
    # --- The below fields are currently valid, but need to be reworked for new search ---------------------------------
    mapping_for_search_filter: str | None = None
    group_by: str | None = None
    group_by_value: str | None = None
    value_mapping: str | None = None
    # ------------------------------------------------------------------------------------------------------------------


class StringFieldConfig(BaseModel):
    enum: list[str] | None


class StringFieldDefinition(BaseFieldDefinition):
    data_type: Literal["string"] = DataTypeField
    config: StringFieldConfig


class BaseNumberFieldConfig(BaseModel):
    units: str


class ManualBinsNumberFieldConfig(BaseNumberFieldConfig):
    bins: list[int | float]


class AutoBinsNumberFieldConfig(BaseNumberFieldConfig):
    bin_size: int
    taper_left: int
    taper_right: int
    minimum: int
    maximum: int


class NumberFieldDefinition(BaseFieldDefinition):
    data_type: Literal["number"] = DataTypeField
    config: ManualBinsNumberFieldConfig | AutoBinsNumberFieldConfig


class DateFieldConfig(BaseModel):
    bin_by: Literal["month"]  # Currently only binning by month is implemented


class DateFieldDefinition(BaseFieldDefinition):
    data_type: Literal["date"] = DataTypeField
    config: DateFieldConfig


FieldDefinition = DateFieldDefinition | NumberFieldDefinition | StringFieldDefinition
