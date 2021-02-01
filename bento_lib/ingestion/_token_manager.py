import secrets
from datetime import datetime, timedelta
from typing import Optional

__all__ = ["IngestionTokenManager"]


class IngestionTokenManager:
    """
    Used by Bento data services to manage one-time use tokens for ingesting
    data. In this fashion, services like WES can call back to the public
    Bento URL without needing to use a general-purpose auth token or internal
    container networking.
    """

    def __init__(self, service_name: str, redis_connection_data: Optional[dict] = None):
        """
        TODO
        :param service_name: TODO
        :param redis_connection_data: TODO
        """

        # TODO: redis stuff (fetching old, etc.)
        self._service_name = service_name
        self._token_registry = {}

    def generate_token(self, expiry=10080) -> str:
        # Default expiry: 7 days (10080 minutes)

        # Generate new token (throw in lots of bits; why not, this doesn't
        # have to be particularly performant.)
        new_token = secrets.token_urlsafe(nbytes=128)

        # Add token to the internal list
        self._token_registry[new_token] = datetime.now() + timedelta(minutes=expiry)

        # TODO: Sync with Redis if possible

        return new_token

    def check_and_consume_token(self, token: str) -> bool:
        """
        Checks if a token is valid (present and not expired.)
        :param token: The token to check
        :return: boolean representing the token's validity
        """
        token_exp = self._token_registry.pop(token, None)
        return token_exp and datetime.now() < token_exp

    def clear_all_tokens(self) -> None:
        """
        Deletes all the tokens in the cache (e.g. in case of a database leak
        while jobs are currently running/tokens are valid.)
        """

        self._token_registry = {}
        # TODO: Sync with Redis if possible
