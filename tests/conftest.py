import pytest
import structlog
from aioresponses import aioresponses
from structlog.testing import LogCapture


@pytest.fixture
def aioresponse():
    with aioresponses() as m:
        yield m


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])
