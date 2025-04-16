from pydantic import BaseModel, Field

__all__ = ["SearchSection"]


class SearchSection(BaseModel):
    """
    Groups search fields into a section with a title,
        e.g., {"section_title": "Demographics", "fields": ["age", "sex"]}
    """

    section_title: str = Field(..., title="Section title")
    fields: list[str] = Field(
        ..., title="Fields", description="A list of field IDs (keys of the fields part of the discovery config)"
    )
