import pathlib
import asyncpg
import pytest
import pytest_asyncio
from bento_lib.db.pg_async import PgAsyncDatabase
from typing import AsyncGenerator


TEST_SCHEMA = pathlib.Path(__file__).parent / "data" / "test.sql"


async def get_test_db() -> AsyncGenerator[PgAsyncDatabase, None]:
    db_instance = PgAsyncDatabase("postgresql://postgres@localhost:5432/postgres", TEST_SCHEMA)
    await db_instance.initialize(pool_size=1)  # Small pool size for testing
    yield db_instance


db_fixture = pytest_asyncio.fixture(get_test_db, name="pg_async_db")


@pytest_asyncio.fixture
async def db_cleanup(pg_async_db: PgAsyncDatabase):
    yield
    conn: asyncpg.Connection
    async with pg_async_db.connect() as conn:
        await conn.execute("DROP TABLE IF EXISTS test_table")
    await pg_async_db.close()


# noinspection PyUnusedLocal
@pytest.mark.asyncio
async def test_pg_async_db_open_close(pg_async_db: PgAsyncDatabase, db_cleanup):
    await pg_async_db.close()
    assert pg_async_db._pool is None

    # duplicate request: should be idempotent
    await pg_async_db.close()
    assert pg_async_db._pool is None

    # should not be able to connect
    conn: asyncpg.Connection
    async with pg_async_db.connect() as conn:
        assert pg_async_db._pool is not None  # Connection auto-initialized
        async with pg_async_db.connect(existing_conn=conn) as conn2:
            assert conn == conn2  # Re-using existing connection should be possible

    # try re-opening
    await pg_async_db.initialize()
    assert pg_async_db._pool is not None
    old_pool = pg_async_db._pool

    # duplicate request: should be idempotent
    await pg_async_db.initialize()
    assert pg_async_db._pool == old_pool  # same instance
