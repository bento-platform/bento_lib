from ._utils import load_json_schema


__all__ = [
    "CHORD_INGEST_SCHEMA",
    "CHORD_DATA_USE_SCHEMA",
]


# TODO: Refactor this schema and semi-combine with workflow schema
CHORD_INGEST_SCHEMA = load_json_schema("chord_ingest.schema.json")

CHORD_DATA_USE_SCHEMA = load_json_schema("chord_data_use.schema.json")
