import configparser
import os

from . import auth
from . import drs
from . import events
from . import schemas
from . import search
from . import service_info
from . import workflows


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), "package.cfg"))


name = config["package"]["name"]
__version__ = config["package"]["version"]
__all__ = ["__version__", "auth", "drs", "events", "schemas", "search", "service_info", "workflows"]
