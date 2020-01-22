import datetime
from functools import partial
from werkzeug.http import HTTP_STATUS_CODES


__all__ = [
    "http_error",

    "bad_request_error",
    "unauthorized_error",
    "forbidden_error",
    "not_found_error",

    "internal_server_error",
    "not_implemented_error",
]


def _error_message(message):
    return {"message": message}


def http_error(code: int, *errors):
    if code not in HTTP_STATUS_CODES:
        print(f"[CHORD Lib] Error: Could not find code {code} in valid HTTP status codes.")
        code = 500
        errors = (*errors, f"An invalid status code of {code} was specified by the service.")

    if code < 400:
        print(f"[CHORD Lib] Error: Code {code} is not an HTTP error code.")
        code = 500
        errors = (*errors, f"A non-error status code of {code} was specified by the service.")

    message = HTTP_STATUS_CODES[code]

    return {
        "code": code,
        "message": message,
        "timestamp": datetime.datetime.utcnow().isoformat("T") + "Z",
        **({"errors": [_error_message(e) for e in errors]} if len(errors) > 0 else {})
    }


_e = partial(partial, http_error)

bad_request_error = _e(400)
unauthorized_error = _e(401)
forbidden_error = _e(403)
not_found_error = _e(404)

internal_server_error = _e(500)
not_implemented_error = _e(501)
