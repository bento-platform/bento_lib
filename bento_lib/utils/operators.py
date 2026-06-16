from functools import partial
from operator import eq, is_, is_not

__all__ = [
    "eq_blank",
    "is_none",
    "is_not_none",
]

eq_blank = partial(eq, "")
is_none = partial(is_, None)
is_not_none = partial(is_not, None)
