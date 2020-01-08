from pkg_resources import get_distribution

from . import auth
from . import events
from . import ingestion
from . import schemas
from . import search
from . import utils
from . import workflows

name = "chord_lib"
__version__ = get_distribution(name).version
__all__ = ["__version__", "auth", "events", "ingestion", "schemas", "search", "utils", "workflows"]
