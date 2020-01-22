from flask import jsonify
from .errors import forbidden_error


__all__ = ["flask_forbidden_error"]


def flask_forbidden_error(*errors):
    return jsonify(forbidden_error(errors)), 403
