from datetime import datetime
from typing import Self

from pydantic import BaseModel, model_validator

__all__ = ["TimeInterval"]


class TimeInterval(BaseModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/time-interval.html
    """
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def check_end_gte_start(self) -> Self:
        if self.end < self.start:
            raise ValueError("high should not be less than low")
        return self
