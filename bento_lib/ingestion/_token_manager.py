import redis
import secrets

from datetime import datetime, timedelta

# TODO: Python 3.9: lowercase dict typing
from typing import Dict, Optional

__all__ = ["IngestionTokenManager"]


class IngestionTokenManager:
    """
    Used by Bento data services to manage one-time use tokens for ingesting
    data. In this fashion, services like WES can call back to the public
    Bento URL without needing to use a general-purpose auth token or internal
    container networking.

    Full rationale is as follows:
     - Needing to support both Singularity and Docker containers puts us in a
       difficult spot, as the internal networking is different
     - Some services (katsu, variant) may be used without others
       (service-registry, etc.) or under different URLs/internal domains/...
     - WES jobs can take a long time, so passing an auth token to a job means
       we can't expire these as fast
     - We may want to trust a service / workflow ONLY for data writing and not
       reading anything in the services
    """

    def __init__(self, service_name: str, redis_connection_data: Optional[dict] = None):
        """
        Initializes an instance of the token manager. If redis_connection_data
        is passed, the contents will be used to initialize a redis-py
        connection. A blank dictionary will use Redis defaults (localhost/6379)
        :param service_name: A unique name (within the Redis instance) for the token set
        :param redis_connection_data: A dictionary with redis-py connection parameters
        """

        self._service_name: str = service_name
        self._token_registry: Dict[str, float] = {}

        self._rc: Optional[redis.Redis] = None

        if redis_connection_data is not None:
            # If the user passed Redis connection information in, we enter
            # "Redis mode" and require that a successful connection be made
            self._rc = redis.Redis(**redis_connection_data, encoding="utf-8")
            self._redis_load()  # Load any cached values

    @property
    def _redis_key(self) -> str:
        """
        Unique key for the Redis token hash set, based on the service name.
        :return: Generated unique key for the Redis hash set
        """
        return f"{self._service_name}_ingest_tokens"

    def _redis_fetch(self) -> dict:
        """
        Loads tokens from Redis and returns them; in the process, any
        tokens that have expired are removed.
        :return: Token dictionary from Redis
        """
        return {
            t.decode("utf-8"): float(e)
            for t, e in self._rc.hgetall(self._redis_key).items()
            if IngestionTokenManager._check_token(float(e))}

    def _redis_load(self):
        """
        Loads tokens from Redis into the in-memory cache; in the process, any
        tokens that have expired are removed.
        """
        self._token_registry = self._redis_fetch()

    def _redis_update(self):
        """
        If a Redis connection has been established, copy all token data from
        the in-memory cache to a Redis hashmap.
        """

        if not self._rc:
            return

        if self._token_registry:
            self._rc.hset(self._redis_key, mapping=self._token_registry)
        else:
            self._rc.delete(self._redis_key)

    def generate_token(self, expiry=10080) -> str:
        """
        Generates a secure one-time use token, with an expiry, to ingest some
        data into a Bento data service.
        :param expiry: Expiry (in minutes) from the current time for the new token
        :return: The newly-generated ingestion token
        """
        # Default expiry: 7 days (10080 minutes)

        # Generate new token (throw in lots of bits; why not, this doesn't
        # have to be particularly performant.)
        new_token = secrets.token_urlsafe(nbytes=128)

        # Add token to the internal list
        self._token_registry[new_token] = (datetime.now() + timedelta(minutes=expiry)).timestamp()

        # Update Redis if connected
        self._redis_update()

        return new_token

    @staticmethod
    def _check_token(token_exp: Optional[float]) -> bool:
        """
        Given a token, checks if the token is valid (i.e. exists in the token
        set and is not expired.)
        :param token_exp: Token expiry, or None if token was not found
        :return: Token validity
        """
        return token_exp and datetime.now().timestamp() < token_exp

    def check_and_consume_token(self, token: str) -> bool:
        """
        Given a token, checks if the token is valid (i.e. exists in the token
        set and is not expired), consuming the token in the process.
        :param token: The token to check
        :return: boolean representing the token's validity
        """
        token_exp = self._token_registry.pop(token, None)
        self._redis_update()
        return IngestionTokenManager._check_token(token_exp)

    def clear_all_tokens(self) -> None:
        """
        Deletes all the tokens in the cache (e.g. in case of a database leak
        while jobs are currently running/tokens are valid.)
        """
        self._token_registry = {}
        self._redis_update()
