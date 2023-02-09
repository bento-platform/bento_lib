from functools import wraps
from flask import current_app

from .middleware import AuthxFlaskMiddleware


def authn_token_required_flask_wrapper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # expecting a globally accessible instance of AuthxFlaskMiddleware
        if valid_authx():
            current_app.authx['middleware'].verify_token_required()
        return f(*args, **kwargs)

    return decorated_function


def authn_token_optional_flask_wrapper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # expecting a globally accessible instance of AuthxFlaskMiddleware
        if valid_authx():
            current_app.authx['middleware'].verify_token_optional()
        return f(*args, **kwargs)

    return decorated_function


def valid_authx():
    if current_app.authx is not None and \
            current_app.authx['enabled'] is not None and \
            current_app.authx['middleware'] is not None and \
            isinstance(current_app.authx['enabled'], bool) and \
            isinstance(current_app.authx['middleware'], AuthxFlaskMiddleware):
        return True
    return False
