from operator import not_

from pydantic import AnyUrl, Field

from .._models import BentoClinPhenModel


class File(BentoClinPhenModel):
    uri: AnyUrl
    individual_to_file_identifiers: dict[str, str] = Field(default_factory=dict, exclude_if=not_)
    file_attributes: dict[str, str] = Field(default_factory=dict, exclude_if=not_)
