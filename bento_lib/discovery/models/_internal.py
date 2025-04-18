from pydantic import ConfigDict

__all__ = ["NoAdditionalProperties"]


class NoAdditionalProperties:
    model_config = ConfigDict(extra="forbid", json_schema_extra={"additionalProperties": False})
