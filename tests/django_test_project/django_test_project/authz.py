from django.conf import settings
from bento_lib.auth.middleware.django import DjangoAuthMiddleware

__all__ = [
    "authz",
    "authz_middleware",
]

middleware_settings = getattr(settings, "BENTO_AUTHZ_MIDDLEWARE_CONFIG", {})

authz = DjangoAuthMiddleware(
    middleware_settings["AUTHZ_SERVICE_URL"],
    middleware_settings.get("DRS_COMPAT", False),
    middleware_settings.get("SR_COMPAT", False),
    settings.DEBUG,
    middleware_settings.get("ENABLED", True),
    middleware_settings.get("LOGGER"),
)
authz_middleware = authz.make_django_middleware()
