import os

from flask import request
from functools import wraps
from typing import Union

from ..responses.flask_errors import flask_forbidden_error
from .roles import *


__all__ = [
    "flask_permissions",
    "flask_permissions_any_user",
    "flask_permissions_owner",
]


# TODO: Centralize this
CHORD_DEBUG = os.environ.get("CHORD_DEBUG", "true").lower() == "true"
CHORD_PERMISSIONS = os.environ.get("CHORD_PERMISSIONS", str(not CHORD_DEBUG)).lower() == "true"


def _check_roles(headers, roles: Union[set, dict]):
    method_roles = roles if not isinstance(roles, dict) else roles.get(request.method, set())
    return not CHORD_PERMISSIONS or len(method_roles) == 0 or all(("X-User" in headers,
                                                                   headers.get("X-User-Role", "") in method_roles))


def flask_permissions(method_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _check_roles(request.headers, method_roles):
                return flask_forbidden_error()
            return func(*args, **kwargs)
        return wrapper
    return decorator


flask_permissions_any_user = flask_permissions({ROLE_USER, ROLE_OWNER})
flask_permissions_owner = flask_permissions({ROLE_OWNER})
