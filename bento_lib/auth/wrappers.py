import os

from functools import wraps
from flask import current_app

from .middleware import AuthxFlaskMiddleware


def authn_token_required_flask_wrapper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # expecting a globally accessible instance of AuthxFlaskMiddleware
        if current_app.authx != None and \
                current_app.authx['enabled'] != None and \
                current_app.authx['middleware'] != None and \
                isinstance(current_app.authx['enabled'], bool) and \
                isinstance(current_app.authx['middleware'], AuthxFlaskMiddleware):
            current_app.authx['middleware'].verify_token()
        return f(*args, **kwargs)

    return decorated_function
