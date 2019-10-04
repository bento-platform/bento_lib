# TODO: URI schemas
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
