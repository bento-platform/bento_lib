from flask import jsonify
from functools import partial
from .errors import *


__all__ = [
    "flask_error",

    "flask_bad_request_error",
    "flask_unauthorized_error",
    "flask_forbidden_error",
    "flask_not_found_error",

    "flask_internal_server_error",
    "flask_not_implemented_error",
]


def flask_error(code: int, *errors):
    return jsonify(http_error(code, *errors)), code


def _flask_error(code: int):
    return partial(flask_error, code)


flask_bad_request_error = _flask_error(400)
flask_unauthorized_error = _flask_error(401)
flask_forbidden_error = _flask_error(403)
flask_not_found_error = _flask_error(404)

flask_internal_server_error = _flask_error(500)
flask_not_implemented_error = _flask_error(501)
