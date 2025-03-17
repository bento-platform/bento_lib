import asyncio

import aiofiles
import asyncpg
import contextlib
from pathlib import Path
from typing import AsyncIterator

__all__ = [
    "PgAsyncDatabaseException",
    "PgAsyncDatabase",
]


class PgAsyncDatabaseException(Exception):
    pass


class PgAsyncDatabase:
    def __init__(self, db_uri: str, schema_path: Path):
        self._db_uri: str = db_uri
        self._schema_path: Path = schema_path

        self._pool: asyncpg.Pool | None = None
        self._pool_init_task: asyncio.Task | None = None
        self._pool_closing_task: asyncio.Task | None = None

    async def initialize(self, pool_size: int = 10) -> bool:
        if self._pool_closing_task:
            raise PgAsyncDatabaseException("Cannot open the pool while it is closing")

        if not self._pool:  # Initialize the connection pool if needed
            if not self._pool_init_task:

                async def _init():
                    pool = await asyncpg.create_pool(self._db_uri, min_size=pool_size, max_size=pool_size)

                    # If we freshly initialized the connection pool, connect to the database and execute the schema
                    # script. Don't use our own self.connect() method, since that'll end up in a circular task await.
                    async with aiofiles.open(self._schema_path, "r") as sf:
                        conn: asyncpg.Connection
                        async with pool.acquire() as conn:
                            async with conn.transaction():
                                await conn.execute(await sf.read())

                    self._pool = pool
                    self._pool_init_task = None

                    return True  # Freshly initialized the pool + executed the schema script

                self._pool_init_task = asyncio.create_task(_init())

            # self._pool_init_task is now guaranteed to not be None - can be awaited
            return await self._pool_init_task

        return False  # Pool already initialized

    async def close(self) -> bool:
        if self._pool_init_task:
            raise PgAsyncDatabaseException("Cannot close the pool while it is opening")

        if self._pool:
            if not self._pool_closing_task:

                async def _close():
                    await self._pool.close()
                    # must come after the "await" in this function, so that we can properly re-use the task that is
                    # checked for IF self._pool is not None:
                    self._pool = None
                    self._pool_closing_task = None
                    return True  # Just closed the pool

                self._pool_closing_task = asyncio.create_task(_close())

            # self._pool_closing_task is now guaranteed to not be None - can be awaited
            return await self._pool_closing_task

        return False  # Pool already closed

    @contextlib.asynccontextmanager
    async def connect(self, existing_conn: asyncpg.Connection | None = None) -> AsyncIterator[asyncpg.Connection]:
        # TODO: raise raise DatabaseError("Pool is not available") when FastAPI has lifespan dependencies
        #  + manage pool lifespan in lifespan fn.

        # If we're currently closing, wait for closing to finish before trying to re-open
        if self._pool_closing_task:
            await self._pool_closing_task

        if self._pool is None:
            # initialize if this is the first time we're using the pool, or wait for existing initialization to finish:
            await self.initialize()

        if existing_conn is not None:
            yield existing_conn
            return

        conn: asyncpg.Connection
        async with self._pool.acquire() as conn:
            yield conn
