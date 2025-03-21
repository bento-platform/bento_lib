import re

from bento_lib import workflows
from pathlib import Path

__all__ = [
    "authz_test_include_patterns",
    "authz_test_exempt_patterns",
    "authz_test_case_params",
    "authz_test_cases",
    "TEST_AUTHZ_VALID_POST_BODY",
    "TEST_AUTHZ_HEADERS",
    "DATA_DIR",
    "SARS_COV_2_FASTA_PATH",
    "WDL_DIR",
    "WORKFLOW_DEF",
]

# cases: (authz response code, authz response result, test client URL, auth header included, assert final response)
authz_test_include_patterns = ((r".*", re.compile(r"^/(get|post).*$")),)
authz_test_exempt_patterns = ((r"POST", re.compile(r"/post-exempted")),)
authz_test_case_params = "authz_code, authz_res, test_url, inc_headers, test_code"
authz_test_cases = (
    # allowed through
    (200, None, "/post-exempted", False, 200),
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

DATA_DIR = Path(__file__).parent / "data"
SARS_COV_2_FASTA_PATH = DATA_DIR / "sars_cov_2.fa"

WDL_DIR = Path(__file__).parent / "wdls"

WORKFLOW_DEF = wd = workflows.models.WorkflowDefinition(
    name="Test Workflow",
    type="ingestion",
    description="A test workflow",
    file="test.wdl",
    inputs=[
        workflows.models.WorkflowStringInput(id="input1", type="string", help="Some string input"),
        workflows.models.WorkflowEnumInput(id="input2", type="enum", values="{{ provider.url }}/list"),
    ],
)
