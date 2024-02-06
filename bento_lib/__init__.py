from importlib import metadata

from . import auth
from . import drs
from . import events
from . import schemas
from . import search
from . import service_info
from . import workflows

__version__ = metadata.version(__name__)
__all__ = ["__version__", "auth", "drs", "events", "schemas", "search", "service_info", "workflows"]
