import configparser
import os

from . import auth
from . import events
from . import ingestion
from . import schemas
from . import search
from . import workflows


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), "package.cfg"))


name = config["package"]["name"]
__version__ = config["package"]["version"]
__all__ = ["__version__", "auth", "events", "ingestion", "schemas", "search", "workflows"]
