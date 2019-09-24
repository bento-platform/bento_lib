# TODO: URI schemas
SERVICE_INFO_SCHEMA = {
    "$id": "https://distributedgenomics.ca/ga4gh/service-info.schema.json",  # TODO: Not a real URL
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "type": {"type": "string"},
        "description": {"type": "string"},
        "organization": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "url": {"type": "string"}
            },
            "required": ["name", "url"]
        },
        "contactUrl": {"type": "string"},
        "documentationUrl": {"type": "string"},
        "createdAt": {"type": "string"},
        "updatedAt": {"type": "string"},
        "environment": {"type": "string"},
        "version": {"type": "string"}
    },
    "required": ["id", "name", "type", "organization", "version"]
}
