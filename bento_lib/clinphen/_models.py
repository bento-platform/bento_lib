from pydantic import BaseModel, ConfigDict

from ._fields import field_name_to_camel

__all__ = ["BentoClinPhenModel"]


class BentoClinPhenModel(BaseModel):
    model_config = ConfigDict(alias_generator=field_name_to_camel)
