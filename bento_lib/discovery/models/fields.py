from pydantic import AliasChoices, BaseModel, Discriminator, Field, Tag, model_validator
from typing import Annotated, Literal

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
    units: str | None = None  # Units are optional - some fields may be numerical but unitless (e.g., a ratio)


class ManualBinsNumberFieldConfig(BaseNumberFieldConfig):
    bins: list[int | float] = Field(..., min_length=2)
    minimum: int | None = None
    maximum: int | None = None

    @model_validator(mode="after")
    def check_bin_config(self) -> "ManualBinsNumberFieldConfig":
        if self.maximum is not None and self.minimum is not None and self.maximum < self.minimum:
            raise ValueError("maximum cannot be less than minimum")

        if self.minimum is not None and self.minimum > self.bins[0]:
            raise ValueError("minimum cannot be greater than first bin")

        if self.maximum is not None and self.maximum < self.bins[-1]:
            raise ValueError("maximum cannot be less than last bin")

        for c in range(1, len(self.bins)):
            if self.bins[c - 1] >= self.bins[c]:
                raise ValueError("bins must be in increasing order")

        return self


class AutoBinsNumberFieldConfig(BaseNumberFieldConfig):
    """
    Configuration for a number field with automatically-generated bins.

    Note: limited to operations on integer values for simplicity.
    A word of caution: when implementing handling of floating point values, be aware of string format (might need to
    add precision to config?) computations of modulo.
    """

    bin_size: int
    taper_left: int
    taper_right: int
    minimum: int
    maximum: int

    @model_validator(mode="after")
    def check_bin_config(self) -> "AutoBinsNumberFieldConfig":
        if self.maximum < self.minimum:
            raise ValueError("maximum cannot be less than minimum")

        if self.taper_right < self.taper_left:
            raise ValueError("taper_right cannot be less than taper_left")

        if self.minimum > self.taper_left:
            raise ValueError("taper_left cannot be less than minimum")

        if self.taper_right > self.maximum:
            raise ValueError("taper_right cannot be greater than maximum")

        if (self.taper_right - self.taper_left) % self.bin_size:
            raise ValueError("range between taper values is not a multiple of bin_size")

        return self


def _number_field_config_discriminator(v: dict | BaseModel) -> str:
    """
    Pydantic supports "discriminated unions" with a callable discriminator, where a function can tell Pydantic which
    member of a union type a dictionary input or instance is, based on the contents of the dict/instance. This is useful
    for type narrowing during validation.

    See also https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminator
    :param v: Either dictionary data to be validated against a model, or an instance of a model.
    :return: "manual" if the passed value is a ManualBinsNumberFieldConfig (or input data for that model),
             "auto" otherwise (AutoBinsNumberFieldConfig).
    """
    return "manual" if (isinstance(v, dict) and "bins" in v) or hasattr(v, "bins") else "auto"


class NumberFieldDefinition(BaseFieldDefinition):
    data_type: Literal["number"] = DataTypeField

    # See https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminator
    # We implement a Pydantic discriminated union, with a callable discriminator to determine which type the input data
    # or instance is - either a manual bin configuration or an automatic bin generator.
    config: Annotated[
        Annotated[ManualBinsNumberFieldConfig, Tag("manual")] | Annotated[AutoBinsNumberFieldConfig, Tag("auto")],
        Discriminator(_number_field_config_discriminator),
    ]


class DateFieldConfig(BaseModel):
    bin_by: Literal["month"]  # Currently only binning by month is implemented


class DateFieldDefinition(BaseFieldDefinition):
    data_type: Literal["date"] = DataTypeField
    config: DateFieldConfig


FieldDefinition = DateFieldDefinition | NumberFieldDefinition | StringFieldDefinition
