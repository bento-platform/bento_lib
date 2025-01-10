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
]


class BaseFieldDefinition(BaseModel):
    mapping: str
    title: str  # TODO: make optional and pull from Bento schema if not set
    description: str  # TODO: make optional and pull from Bento schema if not set
    datatype: Literal["string", "number", "date"] = Field(validation_alias=AliasChoices("data_type", "datatype"))
    # --- The below fields are currently valid, but need to be reworked for new search ---------------------------------
    mapping_for_search_filter: str | None = None
    group_by: str | None = None
    group_by_value: str | None = None
    value_mapping: str | None = None
    # ------------------------------------------------------------------------------------------------------------------


class StringFieldConfig(BaseModel):
    enum: list[str] | None


class StringFieldDefinition(BaseFieldDefinition):
    datatype: Literal["string"]
    config: StringFieldConfig


class BaseNumberFieldConfig(BaseModel):
    units: str


class ManualBinsNumberFieldConfig(BaseNumberFieldConfig):
    bins: list[int]


class AutoBinsNumberFieldConfig(BaseNumberFieldConfig):
    bin_size: int
    taper_left: int
    taper_right: int
    minimum: int
    maximum: int


class NumberFieldDefinition(BaseFieldDefinition):
    datatype: Literal["number"]
    config: ManualBinsNumberFieldConfig | AutoBinsNumberFieldConfig


class DateFieldConfig(BaseModel):
    bin_by: str  # TODO


class DateFieldDefinition(BaseFieldDefinition):
    datatype: Literal["date"]
    config: DateFieldConfig
