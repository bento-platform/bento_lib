from bento_lib.utils.headers import authz_bearer_header


def test_utils_authz_bearer_header():
    assert authz_bearer_header("test_token") == {"Authorization": "Bearer test_token"}
    assert authz_bearer_header("") == {}
    assert authz_bearer_header(None) == {}
