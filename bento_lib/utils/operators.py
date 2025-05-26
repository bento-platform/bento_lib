from functools import partial
from operator import is_not

__all__ = [
    "is_not_none",
]

is_not_none = partial(is_not, None)
