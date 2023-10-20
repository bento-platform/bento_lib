from abc import abstractmethod
from typing import Any


__all__ = ["MarkAuthzDoneMixin"]


class MarkAuthzDoneMixin:
    @staticmethod
    @abstractmethod
    def mark_authz_done(request: Any):  # pragma: no cover
        pass
