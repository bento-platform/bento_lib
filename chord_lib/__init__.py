from pkg_resources import get_distribution

from . import ingestion
from . import schemas
from . import search

name = "chord_lib"
__version__ = get_distribution("chord_lib").version
__all__ = ["__version__", "ingestion", "schemas", "search"]
