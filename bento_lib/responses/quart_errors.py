import sys
import traceback

from quart import jsonify
from functools import partial
from typing import Callable

from bento_lib.responses import errors


__all__ = [
    "quart_error_wrap_with_traceback",
    "quart_error_wrap",

    "quart_error",

    "quart_bad_request_error",
    "quart_unauthorized_error",
    "quart_forbidden_error",
    "quart_not_found_error",

    "quart_internal_server_error",
    "quart_not_implemented_error",
]


# noinspection PyIncorrectDocstring
def quart_error_wrap_with_traceback(fn: Callable, *args, **kwargs) -> Callable:
    """
    Function to wrap quart_* error creators with something that supports the application.register_error_handler method,
    while also printing a traceback. Optionally, the keyword argument service_name can be passed in to make the error
    logging more precise.
    :param fn: The quart error-generating function to wrap
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


def quart_error_wrap(fn: Callable, *args, **kwargs) -> Callable:
    """
    Function to wrap quart_* error creators with something that supports the application.register_error_handler method.
    :param fn: The quart error-generating function to wrap
    :return: The wrapped function
    """
    return lambda _e: fn(*args, **kwargs)


def quart_error(code: int, *errs, drs_compat: bool = False, sr_compat: bool = False):
    return jsonify(errors.http_error(code, *errs, drs_compat=drs_compat, sr_compat=sr_compat)), code


def _quart_error(code: int) -> Callable:
    return partial(quart_error, code)


quart_bad_request_error = _quart_error(400)
quart_unauthorized_error = _quart_error(401)
quart_forbidden_error = _quart_error(403)
quart_not_found_error = _quart_error(404)

quart_internal_server_error = _quart_error(500)
quart_not_implemented_error = _quart_error(501)
