from ._utils import load_json_schema


__all__ = [
    "BENTO_INGEST_SCHEMA",
    "BENTO_DATA_USE_SCHEMA",
]


# TODO: Refactor this schema and semi-combine with workflow schema
BENTO_INGEST_SCHEMA = load_json_schema("bento_ingest.schema.json")

BENTO_DATA_USE_SCHEMA = load_json_schema("bento_data_use.schema.json")
