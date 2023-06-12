__all__ = [
    "BentoAuthException",
]


class BentoAuthException(Exception):
    def __init__(self, message="Unauthorized", status_code=401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
