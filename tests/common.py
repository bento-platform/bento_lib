PERMISSION_INGEST_DATA = "ingest:data"

# cases: (authz response code, authz response result, test client URL, auth header included, assert final response)
authz_test_case_params = "authz_code, authz_res, test_url, inc_headers, test_code"
authz_test_cases = (
    # allowed through
    (200, True, "/post-private", True, 200),
    (200, True, "/post-private-no-flag", True, 200),
    # forbidden
    (200, False, "/post-private", True, 403),
    # error from auth service
    (500, False, "/post-private", True, 500),
    # allowed - no token
    (200, True, "/post-private-no-token", False, 200),
    # allowed - no token required, but one given
    (200, True, "/post-private-no-token", True, 200),
    # missing authz flag set
    (200, True, "/post-missing-authz", True, 403),
)

TEST_AUTHZ_VALID_POST_BODY = {"test1": "a", "test2": "b"}
TEST_AUTHZ_HEADERS = {"Authorization": "Bearer test"}
