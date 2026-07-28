from pydantic import AnyUrl, BaseModel, Field
from typing import Literal

__all__ = ["Logo"]


class Logo(BaseModel):
    """
    Logo resource with optional theme-specific variants.

    Supports light/dark theme variants for optimal display across different UI themes.
    """

    url: AnyUrl
    theme: Literal["light", "dark", "default"] = "default"
    description: str | None = Field(default=None, min_length=1)
    contains_text: bool = Field(
        default=False, description="Whether the logo contains branding text to the left or right of the logo image."
    )
