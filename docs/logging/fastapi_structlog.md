# `bento_lib` – setting up structured logging in FastAPI

## Step 1: Replace logger dependency with a `structlog.stdlib.BoundLogger`:

In your logger dependency definition, replace your `get_logger` function with something similar to the following (this
example was taken from the [Reference service](https://github.com/bento-platform/bento_reference_service)):

```python
import structlog

from bento_lib.logging.structured.configure import configure_structlog_from_bento_config, configure_structlog_uvicorn
from fastapi import Depends
from functools import lru_cache
from typing import Annotated

from .config import ConfigDependency
from .constants import BENTO_SERVICE_KIND

__all__ = [
    "get_logger",
    "LoggerDependency",
]


@lru_cache
def get_logger(config: ConfigDependency) -> structlog.stdlib.BoundLogger:
    configure_structlog_from_bento_config(config)
    configure_structlog_uvicorn()  # If using uvicorn to serve the app

    return structlog.stdlib.get_logger(f"{BENTO_SERVICE_KIND}.logger")


LoggerDependency = Annotated[structlog.stdlib.BoundLogger, Depends(get_logger)]

```

**If you type-hint the logger object elsewhere in your service, make sure to change these type hints from 
`logging.Logger` to `structlog.stdlib.BoundLogger`!**


## Step 2: Configure access logger middleware

In the application `main.py` or equivalent:

```python
from bento_lib.apps.fastapi import BentoFastAPI
# ...
app = BentoFastAPI(
    # ...
    configure_structlog_access_logger=True,  # Set up custom access log middleware to replace the default Uvicorn one
    # ...
)
# ...
```

This internally calls `build_structlog_fastapi_middleware(...)` in `bento_lib.logging.structured.fastapi` and attaches
it as HTTP middleware to the FastAPI application.
