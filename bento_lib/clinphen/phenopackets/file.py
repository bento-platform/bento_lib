from operator import not_
from pydantic import BaseModel, AnyUrl, Field


class File(BaseModel):
    uri: AnyUrl
    individual_to_file_identifiers: dict[str, str] = Field(
        alias="individualToFileIdentifiers", default_factory=dict, exclude_if=not_
    )
    file_attributes: dict[str, str] = Field(alias="fileAttributes", default_factory=dict, exclude_if=not_)
