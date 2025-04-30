from pydantic import BaseModel, Field


class BentoDataTypeServiceListing(BaseModel):
    label: str | None = None
    queryable: bool
    item_schema: dict = Field(..., alias="schema")
    metadata_schema: dict
    id: str
    count: int | None


class BentoDataType(BaseModel):
    service_base_url: str
    data_type_listing: BentoDataTypeServiceListing
