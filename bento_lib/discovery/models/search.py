from pydantic import BaseModel

__all__ = ["SearchSection"]


class SearchSection(BaseModel):
    section_title: str
    fields: list[str]
