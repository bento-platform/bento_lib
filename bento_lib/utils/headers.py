__all__ = [
    "authz_bearer_header",
]


def authz_bearer_header(token: str | None) -> dict[str, str]:
    """
    Returns a dictionary with an authorization bearer token header set if a token is specified (not blank or None);
    otherwise, returns an empty dictionary.
    """
    return {"Authorization": f"Bearer {token}"} if token else {}
