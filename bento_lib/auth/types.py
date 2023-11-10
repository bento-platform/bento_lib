from typing import Type

from ..auth.middleware.mark_authz_done_mixin import MarkAuthzDoneMixin
from ..auth.permissions import Permission

__all__ = [
    "EvaluationResultMatrix",
    "EvaluationResultDict",
    "MarkAuthzDoneType",
]

EvaluationResultMatrix = tuple[tuple[bool, ...], ...]
EvaluationResultDict = tuple[dict[Permission, bool], ...]

# Allow subclass OR instance, since mark_authz_done is a static method:
MarkAuthzDoneType = MarkAuthzDoneMixin | Type[MarkAuthzDoneMixin]
