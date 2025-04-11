from pydantic_core import PydanticCustomError

__all__ = ["DiscoveryValidationError"]


class DiscoveryValidationError(PydanticCustomError):
    def __init__(self, message: str, path: str, log_data: dict):
        self._log_data: dict = log_data
        super().__init__("discovery_validation_error", "{path}: {message}", {"path": path, "message": message})
