from operator import not_

from pydantic import AnyUrl, Field

from .._models import BentoClinPhenModel

__all__ = ["File"]

FIELD_DICT_OR_EMPTY = Field(default_factory=dict, exclude_if=not_)


class File(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/file.html
    """

    uri: AnyUrl
    individual_to_file_identifiers: dict[str, str] = FIELD_DICT_OR_EMPTY
    file_attributes: dict[str, str] = FIELD_DICT_OR_EMPTY
