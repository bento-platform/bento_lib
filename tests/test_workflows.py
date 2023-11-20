import pytest

from bento_lib import workflows
from .common import WDL_DIR, WORKFLOW_DEF


def test_namespaced_input():
    assert workflows.utils.namespaced_input("workflow1", "input") == "workflow1.input"


def test_workflow_set():
    ws = workflows.workflow_set.WorkflowSet(WDL_DIR)

    assert not ws.workflow_exists("test")
    assert ws.get_workflow("test") is None
    assert ws.get_workflow_resource("test") is None

    ws.add_workflow("test", WORKFLOW_DEF)
    assert ws.workflow_exists("test")
    assert ws.get_workflow("test") == WORKFLOW_DEF
    assert ws.get_workflow_resource("test") == "test.wdl"
    assert ws.get_workflow_wdl_path("test") == WDL_DIR / "test.wdl"

    assert ws.workflow_dicts_by_type_and_id()["ingestion"]["test"]["name"] == "Test Workflow"
    assert ws.workflow_dicts_by_id()["test"]["name"] == "Test Workflow"

    with pytest.raises(ValueError):
        ws.add_workflow("test", WORKFLOW_DEF)  # already exists

    wd2 = workflows.models.WorkflowDefinition(
        name="Test Workflow 2",
        type="analysis",
        description="A test workflow",
        data_type="experiment",
        tags=["experiment", "cbioportal"],
        file="test2.wdl",
        inputs=[
            workflows.models.WorkflowStringInput(id="input1", type="string"),
        ]
    )

    ws.add_workflow("test2", wd2)
    assert ws.workflow_exists("test2")

    assert ws.get_workflow_wdl_path("test3") is None  # no test3 workflow
