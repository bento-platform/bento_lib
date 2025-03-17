from django.conf import settings
from bento_lib.auth.middleware.django import DjangoAuthMiddleware
from tests.common import authz_test_exempt_patterns

__all__ = [
    "authz",
    "authz_middleware",
]

middleware_settings = getattr(settings, "BENTO_AUTHZ_MIDDLEWARE_CONFIG", {})

authz = DjangoAuthMiddleware(
    middleware_settings["AUTHZ_SERVICE_URL"],
    drs_compat=middleware_settings.get("DRS_COMPAT", False),
    sr_compat=middleware_settings.get("SR_COMPAT", False),
    debug_mode=settings.DEBUG,
    enabled=middleware_settings.get("ENABLED", True),
    logger=middleware_settings.get("LOGGER"),
    exempt_request_patterns=authz_test_exempt_patterns,
)
authz_middleware = authz.make_django_middleware()
