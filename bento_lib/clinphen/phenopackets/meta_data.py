from datetime import datetime
from operator import not_
from pydantic import BaseModel, Field
from typing import Literal

from bento_lib.ontologies.models import VersionedOntologyResource
from bento_lib.utils.operators import eq_blank
from .external_reference import ExternalReference

__all__ = ["Update", "MetaData"]


class Update(BaseModel):
    timestamp: datetime  # TODO
    updated_by: str = Field(alias="updatedBy", default="", exclude_if=eq_blank)
    comment: str = Field(default="", exclude_if=eq_blank)


class MetaData(BaseModel):
    created: datetime  # TODO
    created_by: str = Field(..., alias="createdBy", min_length=1)
    submitted_by: str = Field(default="", alias="submittedBy", exclude_if=eq_blank)
    resources: list[VersionedOntologyResource] = Field(..., min_length=1)
    updates: list[Update] = Field(default_factory=list, exclude_if=not_)
    phenopacket_schema_version: Literal["2.0"] = Field(default="2.0", alias="phenopacketSchemaVersion")
    external_references: list[ExternalReference] = Field(default_factory=list, exclude_if=not_)
