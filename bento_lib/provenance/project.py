from pydantic import Field
from typing import Literal

from bento_lib.discovery import DiscoveryConfig
from bento_lib.i18n import TranslatableModel

from .common.logo import Logo
from .common.long_description import LongDescription

__all__ = ["ProjectModelBase", "ProjectModel"]


class ProjectModelBase(TranslatableModel):
    """Base project model without id field."""

    schema_version: Literal["1.0"]

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    long_description: LongDescription | None = None

    logos: list[Logo] | None = Field(default=None, min_length=1)

    # Discovery configuration specific to this dataset
    discovery: DiscoveryConfig | None = Field(
        default=None,
        description="Dataset-level discovery configuration; falls back to project/instance config if not set.",
    )


class ProjectModel(ProjectModelBase):
    """Dataset model with required identifier field."""

    identifier: str = Field(
        min_length=1, max_length=128
    )  # if from pcgl, directly inherited, otherwise created in katsu

    @classmethod
    def from_base(cls, base: ProjectModelBase, identifier: str) -> "ProjectModel":
        """Create a ProjectModel from a ProjectModelBase with the given identifier."""
        return cls(identifier=identifier, **base.model_dump())
