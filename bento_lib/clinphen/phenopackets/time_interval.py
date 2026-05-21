from datetime import datetime
from pydantic import BaseModel

__all__ = ["TimeInterval"]


class TimeInterval(BaseModel):
    start: datetime
    end: datetime
