from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Literal

from .types import PossiblyI18nText
from .utils import i18n_value

__all__ = [
    "DataDictionaryField",
    "DataDictionary",
]


# very roughly:
#  - https://www.w3.org/TR/2010/NOTE-curie-20101216/#s_syntax
#  - https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-NCName
CURIE_PATTERN = r"^\[?[a-zA-Z_][a-zA-Z_-.]*:.+\]?$"


class DataDictionaryField(BaseModel):
    key: str = Field(..., min_length=1)
    type: Literal[
        "string",
        "integer",
        "float",
        "date",
        "date-time",
        "time",
        "duration",
        "ontology-class",
        "curie",
        "uri",
        "geojson",
        "geolocation",
    ]
    # TODO: validate not allowed in standard Bento case, or exactly 1 of field in the alternative case:
    is_primary_key: bool = Field(
        default=False,
        title="Is Primary Key",
        description=(
            "Whether this field is the primary key for a set of entities. Not permitted in the standard Bento case."
        ),
    )
    is_required: bool = Field(default_factory=lambda d: d.get("is_primary_key", False), title="Is Required")

    property_class: object | None  # TODO: ontology term
    label: PossiblyI18nText | None  # If None, fall back to key
    description: PossiblyI18nText = ""

    # TODO: object -> ontology class
    unit: object | str | None = None

    @model_validator(mode="after")
    def check_unit(self):
        if self.unit is not None and self.type not in {"string", "integer", "ontology-class"}:
            raise ValueError("unit is not valid for any type except string/integer/ontology-class")

    # categorical:
    #  - in a Bento discovery configuration context, this is equivalent to "config": { "enum": null } on a string field,
    #    meaning (in a Bento discovery context) that the data is categorical but we need to extract already-ingested
    #    categorical values from the database if we wanted to render a bar or pie chart.
    is_categorical: bool = Field(
        default_factory=lambda d: d.get("enum") is not None,  # Must be true if enum is set
        title="Is Categorical",
        description=(
            "Whether the field represents categorical data, even if a predefined list of values (enum) is not "
            "specified."
        ),
    )

    @model_validator(mode="after")
    def check_is_categorical(self):
        if not self.is_categorical and self.enum:
            raise ValueError("is_categorical must be True when enum is set")

        if self.is_categorical and self.type in {"float", "date-time", "time"}:
            raise ValueError(f"is_categorical cannot be True for type {self.type}")

    # TODO: one of the following: enum or pattern
    enum: list | None = Field(
        default=None, title="Enum", description="List of possible (allowed) values for the field."
    )

    @model_validator(mode="after")
    def check_enum(self):
        enum_validator = Draft202012Validator({"type": "array", "items": self.as_json_schema(lang="en")})
        for _ in enum_validator.iter_errors(instance=self.enum or []):
            raise ValueError(f"enum contains type other than {self.type}")

    enum_labels: dict[str | int, PossiblyI18nText] | None  # TODO: only for string | int | float | ontology-class.id

    @model_validator(mode="after")
    def check_enum_labels(self):
        if self.enum_labels is not None and self.enum is None:
            raise ValueError("cannot specify enum_labels but not enum")

        enum_set = set(self.enum or ())

        for k in self.enum_labels:
            if k not in enum_set:
                raise ValueError(f"enum label key '{k}' not in enum")

    pattern: str | None = None  # TODO: pattern meta-pattern? also, should only be for string

    @model_validator(mode="after")
    def check_pattern_presence(self):
        if self.pattern is not None and self.type != "string":
            raise ValueError("pattern can only be specified for string fields")

    # ------------------------------------------------------------------------------------------------------------------

    group: str | None = Field(
        default=None,
        title="Group",
        description="Optional data dictionary field grouping, useful for visualization.",
    )  # TODO: maybe use this for permissions too?

    # ------------------------------------------------------------------------------------------------------------------

    @computed_field
    def json_schema_type(self) -> str | None:
        match self.type:
            case "float":
                return "number"
            case "ontology-class" | "geojson" | "geolocation":
                return "object"
            case "date" | "date-time" | "time" | "duration" | "curie" | "uri":
                return "string"
            case _:
                # default case: type maps exactly to JSON schema type
                return self.type

    @computed_field
    def json_schema_format(self) -> str | None:
        match self.type:
            case "date" | "date-time" | "time" | "duration" | "uri":
                return self.type
            # TODO
            case _:
                return None

    def as_json_schema(self, lang: str) -> dict:
        """
        TODO
        :param lang: TODO
        :return: TODO
        """

        f_desc = i18n_value(self.description, lang)

        pattern: str | None = self.pattern

        properties = None
        required: list[str] | None = None
        additional_properties: bool | None = None

        if self.type == "ontology-class":  # TODO: from ontology class pydantic def.
            properties = {
                "id": {"type": "string", "pattern": CURIE_PATTERN},
                "label": {"type": "string", "minLength": 1},
            }
            required = ["id", "label"]
            additional_properties = False

        if self.type == "curie":
            pattern = CURIE_PATTERN

        return {
            "type": self.json_schema_type,
            **({"description": f_desc} if f_desc else {}),
            **({"enum": self.enum} if self.enum else {}),
            **({"pattern": pattern} if pattern else {}),
            **({"format": self.json_schema_format} if self.json_schema_format else {}),
            # for objects:
            **({"properties": properties} if properties else {}),
            **({"required": required} if required else {}),
            **({"additionalProperties": additional_properties} if additional_properties is not None else {}),
        }


class DataDictionary(BaseModel):
    title: PossiblyI18nText = ""  # Equivalent to Semantic Engine "Schema title"
    description: PossiblyI18nText = ""  # Equivalent to Semantic Engine "Schema description"
    fields: list[DataDictionaryField]  # Equivalent to Semantic Engine attributes
    additional_properties: bool = False

    def as_json_schema(self, lang: str) -> dict:
        """
        Generate a JSON schema representation of the data dictionary, for validating whether JSON object records match
        the data dictionary's described fields.
        :param lang: A language for resolving I18n text objects to specific strings in the schema (descriptions, etc.)
        :return: A JSON schema for validating JSON/dictionary records matching the data dictionary's described fields.
        """

        schema_title = i18n_value(self.title, lang)
        schema_desc = i18n_value(self.description, lang)

        properties = {}
        required = []

        for f in self.fields:
            if f.is_required:
                required.append(f.key)
            properties[f.key] = f.as_json_schema(lang)

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            **({"title": schema_title} if schema_title else {}),
            **({"description": schema_desc} if schema_desc else {}),
            "properties": properties,
            "required": required,
            "additionalProperties": self.additional_properties,
        }

    def as_json_schema_validator(self, lang: str) -> Draft202012Validator:
        """
        Return an instance of a JSON Schema validator for the JSON schema representation of the data dictionary.
        :param lang: A language for resolving I18n text objects to specific strings in the schema (descriptions, etc.)
        :return: A JSON schema validator instance for JSON/dictionary records matching the data dictionary's fields.
        """
        return Draft202012Validator(schema=self.as_json_schema(lang=lang))


# TODO: data dictionary list or set? maybe like a social/demographic "slice" of data, etc. etc.
