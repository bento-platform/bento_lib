from abc import ABC, abstractmethod

__all__ = ["ToSchemaOrgJsonLd"]


class ToSchemaOrgJsonLd(ABC):
    @abstractmethod
    def to_schema_org_json_ld(self) -> dict: ...
