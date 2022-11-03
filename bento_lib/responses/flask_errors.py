import sys
import traceback

from flask import jsonify
from functools import partial
from typing import Callable

from bento_lib.responses import errors


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


# noinspection PyIncorrectDocstring
def flask_error_wrap_with_traceback(fn: Callable, *args, **kwargs) -> Callable:
    """
    Function to wrap flask_* error creators with something that supports the application.register_error_handler method,
    while also printing a traceback. Optionally, the keyword argument service_name can be passed in to make the error
    logging more precise.
    :param fn: The flask error-generating function to wrap
    :return: The wrapped function
    """

    service_name = kwargs.pop("service_name", "Bento Service")

    # TODO: pass exception?
    def handle_error(e):
        print(f"[{service_name}] Encountered error:", file=sys.stderr)
        # TODO: py3.10: print_exception(e)
        traceback.print_exception(type(e), e, e.__traceback__)
        return fn(*args, **kwargs)
    return handle_error


def flask_error_wrap(fn: Callable, *args, **kwargs) -> Callable:
    """
    Function to wrap flask_* error creators with something that supports the application.register_error_handler method.
    :param fn: The flask error-generating function to wrap
    :return: The wrapped function
    """
    return lambda _e: fn(*args, **kwargs)


def flask_error(code: int, *errs, drs_compat: bool = False, sr_compat: bool = False):
    return jsonify(errors.http_error(code, *errs, drs_compat=drs_compat, sr_compat=sr_compat)), code


def _flask_error(code: int) -> Callable:
    return partial(flask_error, code)


flask_bad_request_error = _flask_error(400)
flask_unauthorized_error = _flask_error(401)
flask_forbidden_error = _flask_error(403)
flask_not_found_error = _flask_error(404)

flask_internal_server_error = _flask_error(500)
flask_not_implemented_error = _flask_error(501)
