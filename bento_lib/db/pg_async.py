import aiofiles
import asyncpg
import contextlib
from pathlib import Path
from typing import AsyncIterator


__all__ = [
    "PgAsyncDatabase",
]


class PgAsyncDatabase:

    def __init__(self, db_uri: str, schema_path: Path):
        self._db_uri: str = db_uri
        self._schema_path: Path = schema_path

        self._pool: asyncpg.Pool | None = None

    async def initialize(self, pool_size: int = 10):
        conn: asyncpg.Connection

        if not self._pool:  # Initialize the connection pool if needed
            self._pool = await asyncpg.create_pool(self._db_uri, min_size=pool_size, max_size=pool_size)

        # Connect to the database and execute the schema script
        async with aiofiles.open(self._schema_path, "r") as sf:
            async with self.connect() as conn:
                async with conn.transaction():
                    await conn.execute(await sf.read())

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    @contextlib.asynccontextmanager
    async def connect(self, existing_conn: asyncpg.Connection | None = None) -> AsyncIterator[asyncpg.Connection]:
        # TODO: raise raise DatabaseError("Pool is not available") when FastAPI has lifespan dependencies
        #  + manage pool lifespan in lifespan fn.

        if self._pool is None:
            await self.initialize()  # initialize if this is the first time we're using the pool

        if existing_conn is not None:
            yield existing_conn
            return

        conn: asyncpg.Connection
        async with self._pool.acquire() as conn:
            yield conn
