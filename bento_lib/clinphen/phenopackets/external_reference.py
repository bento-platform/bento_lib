from pydantic import BaseModel, Field

from bento_lib.utils.operators import eq_blank

__all__ = ["ExternalReference"]


class ExternalReference(BaseModel):
    id: str = Field(default="", exclude_if=eq_blank)
    reference: str = Field(default="", exclude_if=eq_blank)
    description: str = Field(default="", exclude_if=eq_blank)
