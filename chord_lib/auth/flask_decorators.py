import os

from flask import request
from functools import wraps

from ..responses.flask_errors import flask_forbidden_error


# TODO: Centralize this
CHORD_DEBUG = os.environ.get("CHORD_DEBUG", "True")


def _check_roles(headers, roles):
    return CHORD_DEBUG or len(roles) == 0 or all(("X-User" in headers, headers.get("X-User-Role", "") in roles))


def flask_permissions_any_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _check_roles(request.headers, {"user", "owner"}):
            return flask_forbidden_error()
        return func(*args, **kwargs)
    return wrapper


def flask_permissions_owner(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _check_roles(request.headers, {"owner"}):
            return flask_forbidden_error()
        return func(*args, **kwargs)
    return wrapper
