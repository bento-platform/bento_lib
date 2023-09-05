import werkzeug.utils

from collections import defaultdict
from pydantic import BaseModel, ConfigDict
from typing import Literal


__all__ = [
    # Input base modles
    "WorkflowBaseInput",
    "WorkflowInjectedInput",
    # Input models
    "WorkflowStringInput",
    "WorkflowStringInput",
    "WorkflowStringArrayInput",
    "WorkflowNumberInput",
    "WorkflowNumberArrayInput",
    "WorkflowBooleanInput",
    "WorkflowEnumInput",
    "WorkflowEnumArrayInput",
    "WorkflowProjectDatasetInput",
    "WorkflowDatasetInput",
    "WorkflowFileInput",
    "WorkflowFileArrayInput",
    "WorkflowReferenceGenomeInput",
    "WorkflowServiceUrlInput",
    # Non-Pydantic classes
    "WorkflowSet",
]


class FrozenBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class WorkflowBaseInput(FrozenBaseModel):
    id: str
    required: bool = True
    type: str


class WorkflowInjectedInput(WorkflowBaseInput):
    injected: Literal[True]


class WorkflowStringInput(WorkflowBaseInput):
    type: Literal["string"]


class WorkflowStringArrayInput(WorkflowBaseInput):
    type: Literal["string[]"]


class WorkflowNumberInput(WorkflowBaseInput):
    type: Literal["number"]


class WorkflowNumberArrayInput(WorkflowBaseInput):
    type: Literal["number[]"]


class WorkflowBooleanInput(WorkflowBaseInput):
    type: Literal["boolean"]


class WorkflowEnumInput(WorkflowBaseInput):
    type: Literal["enum"]
    values: list[str]


class WorkflowEnumArrayInput(WorkflowBaseInput):
    type: Literal["enum[]"]
    values: list[str]
    repeatable: bool = True


class WorkflowProjectDatasetInput(WorkflowBaseInput):
    type: Literal["project:dataset"]


class WorkflowDatasetInput(WorkflowBaseInput):
    type: Literal["dataset"]


class WorkflowFileInput(WorkflowBaseInput):
    # can be sourced from drop box / DRS / workflow outputs, whatever the UI decides works
    type: Literal["file"]
    pattern: str = "*"  # file name regular expression pattern


class WorkflowFileArrayInput(WorkflowBaseInput):
    # can be sourced from drop box / DRS / workflow outputs, whatever the UI decides works
    type: Literal["file[]"]
    pattern: str = "*"  # file name regular expression pattern


class WorkflowReferenceGenomeInput(WorkflowBaseInput):
    type: Literal["ref-genome"]
    # TODO: maybe taxon ID or pattern for filtering; for now just a string


class WorkflowServiceUrlInput(WorkflowInjectedInput):
    type: Literal["service-url"]
    service_kind: str


WorkflowInput = (
    WorkflowStringInput |
    WorkflowStringArrayInput |
    WorkflowNumberInput |
    WorkflowNumberArrayInput |
    WorkflowBooleanInput |
    WorkflowEnumInput |
    WorkflowEnumArrayInput |
    WorkflowProjectDatasetInput |
    WorkflowDatasetInput |
    WorkflowFileInput |
    WorkflowFileArrayInput |
    WorkflowReferenceGenomeInput |
    WorkflowServiceUrlInput
)


WorkflowType = Literal["ingestion", "analysis", "export"]


class WorkflowDefinition(BaseModel):
    """
    Class defining meta-information about a workflow in the context of a Bento node.
    """
    name: str  # Human-readable workflow name
    type: WorkflowType  # One of a few pre-defined values for categorizing workflow type/purpose
    description: str  # Human-readable workflow description
    file: str  # WDL file name
    # Here, inputs defines UI / injected inputs for this workflow. These get transformed into a JSON parameters file
    # which is fed to the WDL workflow description / Cromwell.
    # As such, many of these workflow input types end up mapping to the same WDL type:
    #  - ex. the Bento WorkflowInput types enum/project:datraset/dataset/ref-genome all map to the WDL type String.
    inputs: list[WorkflowInput]


class WorkflowSet:
    """
    A class for constructing a singleton object that stores all workflow descriptions in a particular service.
    """

    def __init__(self):
        self._defs_by_id: dict[str, WorkflowDefinition] = {}

    def add_workflow(self, id_: str, definition: WorkflowDefinition):
        if id_ in self._defs_by_id:
            raise ValueError(f"Workflow with id {id_} already exists")

        self._defs_by_id[id_] = definition

    def get_workflow(self, id_: str) -> WorkflowDefinition | None:
        return self._defs_by_id.get(id_)

    def get_workflow_resource(self, id_: str) -> str:
        return werkzeug.utils.secure_filename(self.get_workflow(id_).file)

    def workflow_exists(self, id_: str) -> bool:
        return id_ in self._defs_by_id

    def workflow_dicts_by_type_and_id(self) -> dict[str, dict[str, dict]]:
        by_type = defaultdict(dict)
        for id_, wf in self._defs_by_id.items():
            by_type[wf.type][id_] = wf.model_dump(mode="json")
        return dict(by_type)

    def workflow_dicts_by_id(self) -> dict[str, WorkflowDefinition]:
        return {k: v.model_dump(mode="json") for k, v in self._defs_by_id.items()}
