from importlib import metadata

from . import (
    apps,
    auth,
    clinphen,
    discovery,
    drs,
    events,
    i18n,
    ontologies,
    provenance,
    schemas,
    search,
    service_info,
    streaming,
    utils,
    workflows,
)

__version__ = metadata.version(__name__)
__all__ = [
    "__version__",
    "apps",
    "auth",
    "clinphen",
    "discovery",
    "drs",
    "events",
    "i18n",
    "ontologies",
    "provenance",
    "schemas",
    "search",
    "service_info",
    "streaming",
    "utils",
    "workflows",
]
