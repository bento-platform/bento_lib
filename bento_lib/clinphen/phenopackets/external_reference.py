from pydantic import Field

from bento_lib.utils.operators import eq_blank

from .._models import BentoClinPhenModel

__all__ = ["ExternalReference"]


class ExternalReference(BentoClinPhenModel):
    id: str = Field(default="", exclude_if=eq_blank)
    reference: str = Field(default="", exclude_if=eq_blank)
    description: str = Field(default="", exclude_if=eq_blank)
