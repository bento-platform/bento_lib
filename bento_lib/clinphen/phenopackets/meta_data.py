from datetime import datetime
from typing import Literal

from pydantic import Field

from bento_lib.ontologies.models import VersionedOntologyResource

from .._fields import FIELD_BLANKABLE, FIELD_LIST_OR_EMPTY
from .._models import BentoClinPhenExtraPropsModel, BentoClinPhenModel
from .external_reference import ExternalReference

__all__ = ["Update", "MetaData"]


class Update(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/update.html#rstupdate
    """

    timestamp: datetime  # TODO
    updated_by: str = FIELD_BLANKABLE
    comment: str = FIELD_BLANKABLE


class MetaData(BentoClinPhenExtraPropsModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/metadata.html
    """

    created: datetime  # TODO
    created_by: str = Field(..., min_length=1)
    submitted_by: str = FIELD_BLANKABLE
    resources: list[VersionedOntologyResource] = Field(..., min_length=1)
    updates: list[Update] = FIELD_LIST_OR_EMPTY
    phenopacket_schema_version: Literal["2.0"] = Field(default="2.0")
    external_references: list[ExternalReference] = FIELD_LIST_OR_EMPTY
