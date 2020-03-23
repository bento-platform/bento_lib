import sys
import traceback

from flask import jsonify
from functools import partial
from typing import Callable

from chord_lib.responses import errors


__all__ = [
    "flask_error_wrap_with_traceback",
    "flask_error_wrap",

    "flask_error",

    "flask_bad_request_error",
    "flask_unauthorized_error",
    "flask_forbidden_error",
    "flask_not_found_error",

    "flask_internal_server_error",
    "flask_not_implemented_error",
]


def flask_error_wrap_with_traceback(fn: Callable, service_name="CHORD Service") -> Callable:
    """
    Function to wrap flask_* error creators with something that supports the application.register_error_handler method,
    while also printing a traceback.
    :param fn: The flask error-generating function to wrap
    :param service_name: The name of the service (for logging purposes)
    :return: The wrapped function
    """
    # TODO: pass exception?
    def handle_error(_e):
        print(f"[{service_name}] Encountered error:", file=sys.stderr)
        traceback.print_exc()
        return fn()
    return handle_error


def flask_error_wrap(fn: Callable) -> Callable:
    """
    Function to wrap flask_* error creators with something that supports the application.register_error_handler method.
    :param fn: The flask error-generating function to wrap
    :return: The wrapped function
    """
    return lambda _e: fn()


def flask_error(code: int, *errs):
    return jsonify(errors.http_error(code, *errs)), code


def _flask_error(code: int) -> Callable:
    return partial(flask_error, code)


flask_bad_request_error = _flask_error(400)
flask_unauthorized_error = _flask_error(401)
flask_forbidden_error = _flask_error(403)
flask_not_found_error = _flask_error(404)

flask_internal_server_error = _flask_error(500)
flask_not_implemented_error = _flask_error(501)
