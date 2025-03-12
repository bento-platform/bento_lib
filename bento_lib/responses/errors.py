from datetime import datetime, timezone
from functools import partial
from typing import Callable
from werkzeug.http import HTTP_STATUS_CODES

from bento_lib._internal import internal_logger
from bento_lib.logging.types import StdOrBoundLogger


__all__ = [
    "http_error",
    # - 400s ------------------------------------
    "bad_request_error",
    "unauthorized_error",
    "forbidden_error",
    "not_found_error",
    "method_not_allowed_error",
    "not_acceptable_error",
    "request_timeout_error",
    "range_not_satisfiable_error",
    # - 500s ------------------------------------
    "internal_server_error",
    "not_implemented_error",
]


def _error_message(message):
    return {"message": message}


def http_error(
    code: int,
    *errors,
    drs_compat: bool = False,
    sr_compat: bool = False,
    beacon_meta_callback: Callable[[], dict] | None = None,
    logger: StdOrBoundLogger | None = None,
):
    """
    Builds a dictionary for an HTTP error JSON response.
    :param code: The error status code to embed in the response.
    :param errors: A list of error descriptions (human-readable) to explain the error.
    :param drs_compat: Whether to generate a GA4GH DRS schema backwards-compatible response.
    :param sr_compat: Whether to generate a GA4GH Service Registry backwards-compatible response.
    :param beacon_meta_callback: Callback for generating GA4GH Beacon V2 backwards-compatible meta field for
           error response. If this is specified, Beacon V2-compatible errors will be enabled.
    :param logger: A logger object to use for internal function error logging.
    :return: A dictionary to encode in JSON for the error response.
    """

    logger = logger or internal_logger

    if code not in HTTP_STATUS_CODES:
        logger.error(f"Could not find code {code} in valid HTTP status codes.")
        code = 500
        errors = (*errors, f"An invalid status code of {code} was specified by the service.")

    if code < 400:
        logger.error(f"Code {code} is not an HTTP error code.")
        code = 500
        errors = (*errors, f"A non-error status code of {code} was specified by the service.")

    message = HTTP_STATUS_CODES[code]

    return {
        "code": code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat("T").split("+")[0] + "Z",
        **({"errors": [_error_message(e) for e in errors]} if errors else {}),
        # The DRS spec has a slightly different error specification - if a
        # compatibility flag is passed in, extra fields are tacked on here.
        **({"status_code": code, "msg": message} if drs_compat else {}),
        # The Service Registry spec *also* has a slightly different error
        # specification; do the same thing as above.
        **(
            {
                "status": code,
                "title": message,
                **({"detail": " | ".join(errors)} if errors else {}),
            }
            if sr_compat
            else {}
        ),
        # ... why so many "standards"? Here's a Beacon V2-compatible error specification
        **(
            {
                "meta": beacon_meta_callback(),
                "error": {
                    "errorCode": code,
                    **({"errorMessage": " | ".join(errors)} if errors else {}),
                },
            }
            if beacon_meta_callback is not None
            else {}
        ),
    }


_e = partial(partial, http_error)

bad_request_error = _e(400)
unauthorized_error = _e(401)
forbidden_error = _e(403)
not_found_error = _e(404)
method_not_allowed_error = _e(405)
not_acceptable_error = _e(406)
request_timeout_error = _e(408)
range_not_satisfiable_error = _e(416)

internal_server_error = _e(500)
not_implemented_error = _e(501)
