import os

from functools import wraps
from quart import request
from typing import Callable, Union

from bento_lib.auth.headers import BENTO_USER_HEADER, BENTO_USER_ROLE_HEADER
from bento_lib.auth.roles import ROLE_OWNER, ROLE_USER
from bento_lib.responses.quart_errors import quart_forbidden_error


__all__ = [
    "quart_permissions",
    "quart_permissions_any_user",
    "quart_permissions_owner",
]


# TODO: Centralize this
BENTO_DEBUG = os.environ.get("CHORD_DEBUG", "true").lower() == "true"
BENTO_PERMISSIONS = os.environ.get("CHORD_PERMISSIONS", str(not BENTO_DEBUG)).lower() == "true"


def _check_roles(headers, roles: Union[set, dict]) -> bool:
    method_roles = roles if not isinstance(roles, dict) else roles.get(request.method, set())
    return (
        not BENTO_PERMISSIONS or
        len(method_roles) == 0 or
        (BENTO_USER_HEADER in headers and headers.get(BENTO_USER_ROLE_HEADER, "") in method_roles)
    )


def quart_permissions(method_roles: Union[set, dict]) -> Callable:
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not _check_roles(request.headers, method_roles):
                return quart_forbidden_error()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


quart_permissions_any_user = quart_permissions({ROLE_USER, ROLE_OWNER})
quart_permissions_owner = quart_permissions({ROLE_OWNER})
