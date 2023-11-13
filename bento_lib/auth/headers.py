# !!! LEGACY FILE !!!

__all__ = [
    "BENTO_USER_HEADER",
    "BENTO_USER_ROLE_HEADER",

    "DJANGO_USER_HEADER",
    "DJANGO_USER_ROLE_HEADER",
]


def _to_django_header(header: str):
    return f"HTTP_{header.replace('-', '_').upper()}"


BENTO_USER_HEADER = "X-User"
BENTO_USER_ROLE_HEADER = "X-User-Role"

DJANGO_USER_HEADER = _to_django_header(BENTO_USER_HEADER)
DJANGO_USER_ROLE_HEADER = _to_django_header(BENTO_USER_ROLE_HEADER)
