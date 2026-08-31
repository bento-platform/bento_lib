from datetime import datetime
from operator import not_
from typing import Literal

from pydantic import Field

from bento_lib.ontologies.models import VersionedOntologyResource

from .._fields import FIELD_BLANKABLE
from .._models import BentoClinPhenModel
from .external_reference import ExternalReference

__all__ = ["Update", "MetaData"]


class Update(BentoClinPhenModel):
    timestamp: datetime  # TODO
    updated_by: str = FIELD_BLANKABLE
    comment: str = FIELD_BLANKABLE


class MetaData(BentoClinPhenModel):
    created: datetime  # TODO
    created_by: str = Field(..., min_length=1)
    submitted_by: str = FIELD_BLANKABLE
    resources: list[VersionedOntologyResource] = Field(..., min_length=1)
    updates: list[Update] = Field(default_factory=list, exclude_if=not_)
    phenopacket_schema_version: Literal["2.0"] = Field(default="2.0")
    external_references: list[ExternalReference] = Field(default_factory=list, exclude_if=not_)
