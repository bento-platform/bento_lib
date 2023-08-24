from pydantic import BaseModel
from typing import Literal


class WorkflowBaseInput(BaseModel):
    id: str
    required: bool
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


class WorkflowDefinition(BaseModel):
    name: str
    description: str
    file: str
    inputs: list[WorkflowInput]


class WorkflowSet(BaseModel):
    ingestion: dict[str, WorkflowDefinition] = []
    analysis: dict[str, WorkflowDefinition] = []
    export: dict[str, WorkflowDefinition] = []
