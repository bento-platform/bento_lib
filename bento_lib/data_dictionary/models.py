from pydantic import BaseModel, Field, computed_field
from typing import Literal

__all__ = [
    "DataDictionaryField",
    "DataDictionary",
]


type PossiblyI18nText = str | dict[str, str]


def i18n_value(v: PossiblyI18nText, lang: str, default: str = "") -> str:
    """
    TODO
    :param v: Possibly-internationalized text (either dictionary of ISO 3166-1 alpha-2 --> text, or just plain text.)
    :param lang: Language (ISO 3166-1 alpha-2)
    :param default: Default value if a language key is not present in an internationalized text dictionary.
    :return: The text value, internationalized if possible.
    """
    if isinstance(v, str):
        return v
    v_vals = tuple(v.values())
    return v.get(lang, v_vals[0] if v_vals else default)


class DataDictionaryField(BaseModel):
    key: str = Field(..., min_length=1)
    property_class: object | None  # TODO: ontology term
    type: Literal["string", "integer", "float", "date", "datetime", "ontology_class", "curie", "geojson", "geolocation"]
    label: PossiblyI18nText | None  # If None, fall back to key
    required: bool = False
    description: PossiblyI18nText = ""
    unit: object | str | None = None
    # TODO: defaults to False unless enum is set, but can be overridden to True even with no specified enum:
    categorical: bool
    # TODO: one of the following
    enum: list | None = None  # TODO: validate against data type
    enum_labels: dict[str | int, PossiblyI18nText]  # TODO: only for string | int | float | ontology_class.id
    pattern: str | None  # TODO: pattern meta-pattern?
    # ---
    group: str | None = Field(
        default=None,
        title="Group",
        description="Optional data dictionary field grouping, useful for visualization.",
    )

    @computed_field
    def json_schema_type(self) -> str | None:
        match self.type:
            case "float":
                return "number"
            case "ontology_class" | "geojson" | "geolocation":
                return "object"
            case "date" | "datetime" | "curie":
                return "string"
            case _:
                # default case: type maps exactly to JSON schema type
                return self.type

    @computed_field
    def json_schema_format(self) -> str | None:
        match self.type:
            # TODO
            case _:
                return None


class DataDictionary(BaseModel):
    title: PossiblyI18nText = ""
    description: PossiblyI18nText = ""
    fields: list[DataDictionaryField]
    additional_properties: bool = False

    def as_json_schema(self, lang: str) -> dict:
        """
        TODO
        :param lang: TODO
        :return: TODO
        """

        schema_title = i18n_value(self.title, lang)
        schema_desc = i18n_value(self.description, lang)

        properties = {}
        required = []

        for f in self.fields:
            if f.required:
                required.append(f.key)

            f_desc = i18n_value(f.description, lang)

            properties[f.key] = {
                "type": f.json_schema_type,
                **({"description": f_desc} if f_desc else {}),
                **({"enum": f.enum} if f.enum else {}),
                **({"pattern": f.pattern} if f.pattern else {}),
                **({"format": f.json_schema_format} if f.json_schema_format else {}),
            }

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            **({"title": schema_title} if schema_title else {}),
            **({"description": schema_desc} if schema_desc else {}),
            "properties": properties,
            "required": required,
            "additionalProperties": self.additional_properties,
        }
