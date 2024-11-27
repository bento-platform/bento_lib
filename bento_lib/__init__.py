from importlib import metadata

from . import apps
from . import auth
from . import discovery
from . import drs
from . import events
from . import schemas
from . import search
from . import service_info
from . import streaming
from . import workflows

__version__ = metadata.version(__name__)
__all__ = [
    "__version__",
    "apps",
    "auth",
    "discovery",
    "drs",
    "events",
    "schemas",
    "search",
    "service_info",
    "streaming",
    "workflows",
]
