import werkzeug.utils

from chord_lib import workflows

TEST_WORKFLOWS = {
    "ingestion": {
        "test": {
            "file": "test.wdl"
        }
    },
    "analysis": {
        "test_analysis": {
            "file": "../../../test analysis.wdl"
        }
    }
}


def test_secure_filename():
    assert workflows.secure_filename("../../test file.exe") == werkzeug.utils.secure_filename("../../test file.exe")


def test_workflow_exists():
    assert workflows.workflow_exists("test", TEST_WORKFLOWS)
    assert workflows.workflow_exists("test_analysis", TEST_WORKFLOWS)
    assert not workflows.workflow_exists("does_not_exist", TEST_WORKFLOWS)


def test_get_workflow():
    assert workflows.get_workflow("test", TEST_WORKFLOWS) == TEST_WORKFLOWS["ingestion"]["test"]
    assert workflows.get_workflow("test_analysis", TEST_WORKFLOWS) == TEST_WORKFLOWS["analysis"]["test_analysis"]


def test_get_workflow_resource():
    assert workflows.get_workflow_resource("test", TEST_WORKFLOWS) == "test.wdl"
    assert workflows.get_workflow_resource("test_analysis", TEST_WORKFLOWS) == "test_analysis.wdl"
