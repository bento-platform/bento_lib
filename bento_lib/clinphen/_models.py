from pydantic import BaseModel, ConfigDict

from ._fields import FIELD_DICT_OR_EMPTY, field_name_to_camel

__all__ = ["BentoClinPhenModel", "BentoClinPhenExtraPropsModel"]


class BentoClinPhenModel(BaseModel):
    model_config = ConfigDict(alias_generator=field_name_to_camel)


class BentoClinPhenExtraPropsModel(BentoClinPhenModel):
    extra_properties: dict = FIELD_DICT_OR_EMPTY  # TODO
