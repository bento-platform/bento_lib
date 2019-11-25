# TODO: URI schemas
# TODO: Refactor this schema and semi-combine with workflow schema
CHORD_INGEST_SCHEMA = {
    "$id": "TODO",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "CHORD Ingestion Endpoint",
    "type": "object",
    "required": ["dataset_id", "workflow_id", "workflow_metadata", "workflow_outputs", "workflow_params"],
    "properties": {
        "dataset_id": {
            "type": "string"
        },
        "workflow_id": {
            "type": "string"
        },
        "workflow_metadata": {
            "type": "object",
            "properties": {
                "inputs": {
                    "type": "array"
                },
                "outputs": {
                    "type": "array"
                }
            }
        },
        "workflow_outputs": {
            "type": "object"
        },
        "workflow_params": {
            "type": "object"
        }
    }
}


# TODO: URI schemas
CHORD_DATA_USE_SCHEMA = {
    "$id": "https://bitbucket.org/genap/chord_project_service/raw/master/data_use.schema.json",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "CHORD Data Use File",
    "description": "Schema defining data usage conditions from the GA4GH DUO ontology.",
    "type": "object",
    "properties": {
        "consent_code": {
            "type": "object",
            "properties": {
                "primary_category": {
                    "$ref": "#/definitions/cc_primary_category"
                },
                "secondary_categories": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/cc_secondary_category"
                    }
                }
            },
            "required": ["primary_category", "secondary_categories"],
            "additionalProperties": False
        },
        "data_use_requirements": {
            "type": "array",
            "items": {
                "$ref": "#/definitions/data_use_requirement"
            }
        }
    },
    "required": ["consent_code", "data_use_requirements"],
    "additionalProperties": False,
    "definitions": {
        "cc_primary_category": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["GRU", "GRU-CC", "HMB", "HMB-CC", "DS", "DS-CC", "POA", "NRES"]
                },
                "data": {
                    "type": "object"
                }
            },
            "required": ["code"],
            "additionalProperties": False
        },
        "cc_secondary_category": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["GSO", "NGMR", "RS", "RU"]
                },
                "data": {
                    "type": "object"
                }
            },
            "required": ["code"],
            "additionalProperties": False
        },
        "data_use_requirement": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["COL", "IRB", "GS", "IS", "NPU", "PS", "MOR", "PUB", "RTN", "TS", "US"]
                },
                "data": {
                    "type": "object"
                }
            },
            "required": ["code"],
            "additionalProperties": False
        }
    }
}
