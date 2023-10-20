from typing import Type

from ..auth.middleware.base import MarkAuthzDoneMixin

__all__ = [
    "EvaluationResultMatrix",
    "MarkAuthzDoneType",
]

EvaluationResultMatrix = tuple[tuple[bool, ...], ...]

# Allow subclass OR instance, since mark_authz_done is a static method:
MarkAuthzDoneType = MarkAuthzDoneMixin | Type[MarkAuthzDoneMixin]
