import pytest
import pytest_asyncio
import structlog
from aiointercept import aiointercept
from structlog.testing import LogCapture


@pytest_asyncio.fixture
async def aio():
    async with aiointercept(mock_external_urls=True) as m:
        yield m


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])


pytest_plugins = ["tests.provenance.conftest", "tests.i18n.conftest"]
