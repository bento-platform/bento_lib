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
    # Workflow definition model
    "WorkflowDefinition",
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
