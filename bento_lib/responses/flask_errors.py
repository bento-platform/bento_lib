import traceback

from flask import jsonify, request
from functools import partial
from typing import Callable

from .._internal import internal_logger
from ..auth.types import MarkAuthzDoneType
from ..logging.types import StdOrBoundLogger
from ..responses import errors


__all__ = [
    "flask_error_wrap_with_traceback",
    "flask_error_wrap",
    # -------------------------------------------
    "flask_error",
    # -------------------------------------------
    "flask_bad_request_error",
    "flask_unauthorized_error",
    "flask_forbidden_error",
    "flask_not_found_error",
    "flask_method_not_allowed_error",
    "flask_not_acceptable_error",
    "flask_request_timeout_error",
    "flask_range_not_satisfiable_error",
    # -------------------------------------------
    "flask_internal_server_error",
    "flask_not_implemented_error",
]


# noinspection PyIncorrectDocstring
def flask_error_wrap_with_traceback(fn: Callable, *args, **kwargs) -> Callable:
    """
    Function to wrap flask_* error creators with something that supports the application.register_error_handler method,
    while also printing a traceback.
    :param fn: The flask error-generating function to wrap
    :return: The wrapped function
    """

    logger: StdOrBoundLogger = kwargs.pop("logger", internal_logger)
    authz: MarkAuthzDoneType | None = kwargs.pop("authz", None)

    def handle_error(e):
        logger.error(f"Encountered error:\n{traceback.format_exception(type(e), e, e.__traceback__)}")
        if authz:
            authz.mark_authz_done(request)
        return fn(str(e), *args, **kwargs)

    return handle_error


def flask_error_wrap(fn: Callable, *args, **kwargs) -> Callable:
    """
    Function to wrap flask_* error creators with something that supports the application.register_error_handler method
    and pass in the exception as a message.
    :param fn: The flask error-generating function to wrap
    :return: The wrapped function
    """

    authz: MarkAuthzDoneType | None = kwargs.pop("authz", None)

    def handle_error(e):
        if authz:
            authz.mark_authz_done(request)
        return fn(str(e), *args, **kwargs)

    return handle_error


def flask_error(code: int, *errs, **kwargs):
    return jsonify(errors.http_error(code, *errs, **kwargs)), code


def _flask_error(code: int) -> Callable:
    return partial(flask_error, code)


flask_bad_request_error = _flask_error(400)
flask_unauthorized_error = _flask_error(401)
flask_forbidden_error = _flask_error(403)
flask_not_found_error = _flask_error(404)
flask_method_not_allowed_error = _flask_error(405)
flask_not_acceptable_error = _flask_error(406)
flask_request_timeout_error = _flask_error(408)
flask_range_not_satisfiable_error = _flask_error(416)

flask_internal_server_error = _flask_error(500)
flask_not_implemented_error = _flask_error(501)
