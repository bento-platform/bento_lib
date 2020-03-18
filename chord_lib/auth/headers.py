__all__ = [
    "CHORD_USER_HEADER",
    "CHORD_USER_ROLE_HEADER",

    "DJANGO_USER_HEADER",
    "DJANGO_USER_ROLE_HEADER",
]


def _to_django_header(header: str):
    return f"HTTP_{header.replace('-', '_').upper()}"


CHORD_USER_HEADER = "X-User"
CHORD_USER_ROLE_HEADER = "X-User-Role"

DJANGO_USER_HEADER = _to_django_header(CHORD_USER_HEADER)
DJANGO_USER_ROLE_HEADER = _to_django_header(CHORD_USER_ROLE_HEADER)
