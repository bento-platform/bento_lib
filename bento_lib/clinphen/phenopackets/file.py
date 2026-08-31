from pydantic import AnyUrl

from .._fields import FIELD_DICT_OR_EMPTY
from .._models import BentoClinPhenModel

__all__ = ["File"]


class File(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/file.html
    """

    uri: AnyUrl
    individual_to_file_identifiers: dict[str, str] = FIELD_DICT_OR_EMPTY
    file_attributes: dict[str, str] = FIELD_DICT_OR_EMPTY
