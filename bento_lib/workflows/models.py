import werkzeug.utils

from collections import defaultdict
from pydantic import BaseModel, ConfigDict
from typing import Literal


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


class WorkflowDropBoxFileInput(WorkflowBaseInput):
    type: Literal["drop-box-file"]
    pattern: str = "*"  # file name regular expression pattern


class WorkflowDropBoxFileArrayInput(WorkflowBaseInput):
    type: Literal["drop-box-file[]"]
    pattern: str = "*"  # file name regular expression pattern


class WorkflowDRSBlobInput(WorkflowBaseInput):
    type: Literal["drs-blob"]
    pattern: str = "*"  # file/blob name regular expression pattern


class WorkflowDRSBundleInput(WorkflowBaseInput):
    type: Literal["drs-bundle"]
    pattern: str = "*"  # bundle name regular expression pattern


class WorkflowDRSObjectInput(WorkflowBaseInput):
    type: Literal["drs-object"]
    pattern: str = "*"  # object name regular expression pattern


class WorkflowReferenceGenomeInput(WorkflowBaseInput):
    # TODO: maybe taxon ID or pattern for filtering
    pass


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
    WorkflowDropBoxFileInput |
    WorkflowDropBoxFileArrayInput |
    WorkflowDRSBlobInput |
    WorkflowDRSBundleInput |
    WorkflowDRSObjectInput |
    WorkflowReferenceGenomeInput |
    WorkflowServiceUrlInput
)


WorkflowType = Literal["ingestion", "analysis", "export"]


class WorkflowDefinition(BaseModel):
    name: str
    type: WorkflowType
    description: str
    file: str
    inputs: list[WorkflowInput]


class WorkflowSet:
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
