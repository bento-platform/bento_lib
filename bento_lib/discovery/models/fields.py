from pydantic import BaseModel, Discriminator, Field, RootModel, Tag, model_validator
from typing import Annotated, Literal
from typing_extensions import Self  # TODO: py3.11+ from typing
from ._internal import NoAdditionalProperties

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


DataTypeField = Field(
    ...,
    title="Data type",
    description="Data type of the field (string, number, or date).",
)


class BaseFieldDefinition(BaseModel, NoAdditionalProperties):
    # TODO: constrained type with regular expressions
    mapping: str = Field(
        ...,
        title="Mapping",
        description=(
            "Slash-delimited field mapping, i.e., a path to a field in a discovery-enabled Bento clinical/phenotypic/"
            "experimental data model."
        ),
    )
    # TODO: make optional and pull from Bento schema if not set:
    title: str = Field(..., title="Title", description="Field title")
    # TODO: make optional and pull from Bento schema if not set:
    description: str = Field(..., title="Description", description="Field description")
    datatype: Literal["string", "number", "date"] = DataTypeField
    # --- The below fields are currently valid, but need to be reworked for new search ---------------------------------
    mapping_for_search_filter: str | None = None
    group_by: str | None = None
    group_by_value: str | None = None
    value_mapping: str | None = None
    # ------------------------------------------------------------------------------------------------------------------


class StringFieldConfig(BaseModel, NoAdditionalProperties):
    enum: list[str] | None = Field(
        ...,
        title="Enum",
        description=(
            "Possible values for this string field which can be used for filtering. If null, these will be "
            "auto-populated from data service(s), excluding values which have counts below or at the threshold set in "
            "the discovery rules."
        ),
    )


class StringFieldDefinition(BaseFieldDefinition, NoAdditionalProperties):
    """
    Defines a string field for discovery purposes, including configuration for chart/filter values (`config.enum`).
    """

    datatype: Literal["string"] = DataTypeField
    config: StringFieldConfig = Field(..., title="Config", description="Additional configuration for the string field.")


class BaseNumberFieldConfig(BaseModel, NoAdditionalProperties):
    units: str | None = Field(
        default=None,
        title="Units",
        description=(
            "Units for the number field, e.g., mL, cm, or kg/m^2. Units are optional, as some fields may be numerical "
            "but unitless, e.g., a ratio."
        ),
    )


class ManualBinsNumberFieldConfig(BaseNumberFieldConfig, NoAdditionalProperties):
    """
    Number field configuration with custom chart/search histogram bins.
    It expects a list of bin boundaries `bins`, and optionally `minimum` and `maximum`.

    There are three broad cases for a lower or upper boundary of the bin range, depending on the value of the
    lowest/highest bin and minimum/maximum. For instance, the following cases apply to the lower boundary:

        If minimum is None, the minimum is unbounded:
            so given {"bins": [2, 4, 6, ...]}, the generated bins are:
                <2   [2, 4)   [4, 6)   ...
        If minimum is set to a value below the lowest bin, this extra bin includes only values in [minimum, lowest bin):
            so given {"minimum": 1, "bins": [2, 4, 6, ...]}, the generated bins are:
                <2*  [2, 4)   [4, 6)   ...
                *but only includes values in [1, 2)
        If minimum is equal to the lowest bin, there will not be this extra bin:
            so given {"minimum": 2, "bins": [2, 4, 6, ...]}, the generated bins are:
                [2, 4)   [4, 6)   ...

    This same general logic is mirrored for the maximum and largest bin.
    """

    bins: list[int | float] = Field(
        ...,
        min_length=2,
        title="Bins",
        description=(
            "List of bins for the number field, for filtering and histogram rendering. Bins must be be sorted "
            "smallest-to-largest and must be increasing, i.e., two bins cannot have the same value."
        ),
    )
    minimum: int | None = Field(None, title="Minimum", description="Minimum value to include in binned data")
    maximum: int | None = Field(None, title="Maximum", description="Maximum value to include in binned data")

    @model_validator(mode="after")
    def check_bin_config(self) -> Self:
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


class AutoBinsNumberFieldConfig(BaseNumberFieldConfig, NoAdditionalProperties):
    """
    Configuration for a number field with automatically-generated bins.

    There are two broad cases for a lower or upper boundary of the bin range, depending on the value of the
    lowest/highest bin and taper_left/right. For instance, the following cases apply to the lower boundary:

        If minimum == taper_left, bins are generated from taper_left to taper_right:
            so given {"minimum": 5, "taper_left": 5, "bin_size": 10, ...}, the generated bins are:
                [5, 15)   [15, 25)   [25, 35)   ...
        If minimum < taper_left, an "everything below taper_left" bin is added for values within [minumum, taper_left):
            so given {"minimum": 0, "taper_left": 5, "bin_size": 10, ...}, the generated bins are:
                <5*  [5, 15)   [15, 25)   [25, 35)   ...
                *but only includes values in [0, 5)

    Note: limited to operations on integer values for simplicity.
    A word of caution: when implementing handling of floating point values, be aware of string format (might need to
    add precision to config?) computations of modulo.
    """

    bin_size: int = Field(..., title="Bin size", description="How wide to make the automatically-generated bins")
    taper_left: int = Field(
        ..., title="Taper left", description="Upper limit (exclusive) of smallest bin, unless minimum = taper_left."
    )
    taper_right: int = Field(
        ..., title="Taper right", description="Lower limit (inclusive) of largest bin, unless maximum = taper_right."
    )
    minimum: int = Field(..., title="Minimum", description="Minimum value to include in binned data")
    maximum: int = Field(..., title="Maximum", description="Maximum value to include in binned data")

    @model_validator(mode="after")
    def check_bin_config(self) -> Self:
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


class NumberFieldDefinition(BaseFieldDefinition, NoAdditionalProperties):
    """
    Defines a number field for discovery purposes, including configuration for value binning to generate histograms.
    """

    datatype: Literal["number"] = DataTypeField

    # See https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminator
    # We implement a Pydantic discriminated union, with a callable discriminator to determine which type the input data
    # or instance is - either a manual bin configuration or an automatic bin generator.
    config: Annotated[
        Annotated[ManualBinsNumberFieldConfig, Tag("manual")] | Annotated[AutoBinsNumberFieldConfig, Tag("auto")],
        Discriminator(_number_field_config_discriminator),
    ] = Field(..., title="Config", description="Additional configuration for the number field.")


class DateFieldConfig(BaseModel, NoAdditionalProperties):
    # Currently only binning by month is implemented:
    bin_by: Literal["month"] = Field(
        ...,
        title="Bin by",
        description="Specifies how to bin the date field for filtering and chart rendering.",
    )


class DateFieldDefinition(BaseFieldDefinition, NoAdditionalProperties):
    """
    Defines a number field for discovery purposes, including date binning configuration.
    """

    datatype: Literal["date"] = DataTypeField
    config: DateFieldConfig = Field(..., title="Config", description="Additional configuration for the date field.")


class FieldDefinition(RootModel):
    """
    Field definition model - discriminated union of data/number/string fields, based on datatype property.
    """

    root: DateFieldDefinition | NumberFieldDefinition | StringFieldDefinition = Field(..., discriminator="datatype")

    def __getattr__(self, item):
        return getattr(self.root, item)

    def __setattr__(self, key, value):
        return setattr(self.root, key, value)
