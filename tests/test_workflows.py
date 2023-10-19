import pytest

from bento_lib import workflows


def test_namespaced_input():
    assert workflows.utils.namespaced_input("workflow1", "input") == "workflow1.input"


def test_workflow_set():
    ws = workflows.workflow_set.WorkflowSet()

    assert not ws.workflow_exists("test")
    assert ws.get_workflow("test") is None
    assert ws.get_workflow_resource("test") is None

    wd = workflows.models.WorkflowDefinition(
        name="Test Workflow",
        type="ingestion",
        description="A test workflow",
        file="test.wdl",
        inputs=[
            workflows.models.WorkflowStringInput(id="input1", type="string"),
        ]
    )

    ws.add_workflow("test", wd)
    assert ws.workflow_exists("test")
    assert ws.get_workflow("test") == wd
    assert ws.get_workflow_resource("test") == "test.wdl"

    assert ws.workflow_dicts_by_type_and_id()["ingestion"]["test"]["name"] == "Test Workflow"
    assert ws.workflow_dicts_by_id()["test"]["name"] == "Test Workflow"

    with pytest.raises(ValueError):
        ws.add_workflow("test", wd)  # already exists

    wd2 = workflows.models.WorkflowDefinition(
        name="Test Workflow 2",
        type="analysis",
        description="A test workflow",
        tags=["experiment", "cbioportal"],
        file="test.wdl",
        inputs=[
            workflows.models.WorkflowStringInput(id="input1", type="string"),
        ]
    )

    ws.add_workflow("test2", wd2)
    assert ws.workflow_exists("test2")
