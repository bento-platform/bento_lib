from ._utils import load_json_schema


__all__ = [
    "BENTO_DATA_USE_SCHEMA",
]


BENTO_DATA_USE_SCHEMA = load_json_schema("bento_data_use.schema.json")
