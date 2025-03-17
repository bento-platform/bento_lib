import asyncio
import pathlib
import asyncpg
import pytest
import pytest_asyncio
from bento_lib.db.pg_async import PgAsyncDatabaseException, PgAsyncDatabase
from typing import AsyncGenerator


TEST_SCHEMA = pathlib.Path(__file__).parent / "data" / "test.sql"


async def get_test_db() -> AsyncGenerator[PgAsyncDatabase, None]:
    db_instance = PgAsyncDatabase("postgresql://postgres@localhost:5432/postgres", TEST_SCHEMA)
    await db_instance.initialize(pool_size=1)  # Small pool size for testing
    yield db_instance


db_fixture = pytest_asyncio.fixture(get_test_db, name="pg_async_db")


async def get_test_db_no_init() -> AsyncGenerator[PgAsyncDatabase, None]:
    db_instance = PgAsyncDatabase("postgresql://postgres@localhost:5432/postgres", TEST_SCHEMA)
    yield db_instance


db_fixture_no_init = pytest_asyncio.fixture(get_test_db_no_init, name="pg_async_db_no_init")


@pytest_asyncio.fixture
async def db_cleanup(pg_async_db: PgAsyncDatabase):
    yield
    conn: asyncpg.Connection
    async with pg_async_db.connect() as conn:
        await conn.execute("DROP TABLE IF EXISTS test_table")
    await pg_async_db.close()


@pytest_asyncio.fixture
async def db_cleanup_no_init(pg_async_db_no_init: PgAsyncDatabase):
    yield
    conn: asyncpg.Connection
    async with pg_async_db_no_init.connect() as conn:
        await conn.execute("DROP TABLE IF EXISTS test_table")
    await pg_async_db_no_init.close()


# noinspection PyUnusedLocal
@pytest.mark.asyncio
async def test_pg_async_db_close_auto_open(pg_async_db: PgAsyncDatabase, db_cleanup):
    r = await pg_async_db.close()
    assert r  # did in fact close the pool
    assert pg_async_db._pool is None

    # duplicate request: should be idempotent
    r = await pg_async_db.close()
    assert not r  # didn't close the pool, since it was already closed.
    assert pg_async_db._pool is None

    conn: asyncpg.Connection
    async with pg_async_db.connect() as conn:
        assert pg_async_db._pool is not None  # Connection auto-initialized
        async with pg_async_db.connect(existing_conn=conn) as conn2:
            assert conn == conn2  # Re-using existing connection should be possible


@pytest.mark.asyncio
async def test_pg_async_db_open(pg_async_db_no_init: PgAsyncDatabase, db_cleanup_no_init):
    # try opening
    r = await pg_async_db_no_init.initialize(pool_size=1)
    assert r
    assert pg_async_db_no_init._pool is not None
    old_pool = pg_async_db_no_init._pool

    # duplicate request: should be idempotent
    r = await pg_async_db_no_init.initialize()
    assert not r  # didn't actually initialize the pool; re-used the old object
    assert pg_async_db_no_init._pool == old_pool  # same instance


@pytest.mark.asyncio
async def test_pg_async_db_parallel_open(pg_async_db_no_init: PgAsyncDatabase, db_cleanup):
    # start opening in one coroutine, check with the other - should re-use task
    c = pg_async_db_no_init.initialize(pool_size=1)
    c2 = pg_async_db_no_init.initialize(pool_size=1)
    assert await asyncio.gather(c, c2) == [True, True]


@pytest.mark.asyncio
async def test_pg_async_db_parallel_close(pg_async_db: PgAsyncDatabase, db_cleanup):
    # start closing in one coroutine, check with the other - should re-use task
    c = pg_async_db.close()
    c2 = pg_async_db.close()
    assert await asyncio.gather(c, c2) == [True, True]  # should both internally use the same coroutine & return True


@pytest.mark.asyncio
async def test_pg_async_db_parallel_exc_close_while_opening(pg_async_db_no_init: PgAsyncDatabase, db_cleanup):
    # while opening, try closing - should trigger error
    with pytest.raises(PgAsyncDatabaseException) as e:
        await asyncio.gather(pg_async_db_no_init.initialize(), pg_async_db_no_init.close())

    assert str(e.value) == "Cannot close the pool while it is opening"


@pytest.mark.asyncio
async def test_pg_async_db_parallel_exc_open_while_closing(pg_async_db: PgAsyncDatabase, db_cleanup):
    # while closing, try opening - should trigger error
    with pytest.raises(PgAsyncDatabaseException) as e:
        await asyncio.gather(pg_async_db.close(), pg_async_db.initialize())

    assert str(e.value) == "Cannot open the pool while it is closing"


@pytest.mark.asyncio
async def test_pg_async_db_parallel_exc_close_then_connect(pg_async_db: PgAsyncDatabase, db_cleanup):
    # connect should wait for the pool to close, then re-open it
    async def _c():
        async with pg_async_db.connect():
            pass

    await asyncio.gather(pg_async_db.close(), _c())
    assert pg_async_db._pool is not None
