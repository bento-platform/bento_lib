from pydantic import BaseModel, Field
from typing import Literal

__all__ = ["LongDescription"]


class LongDescription(BaseModel):
    """Extended description with content type specification."""

    content: str = Field(min_length=1)
    content_type: Literal["text/html", "text/markdown", "text/plain"]
