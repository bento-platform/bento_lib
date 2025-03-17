from pydantic import BaseModel, ConfigDict, field_serializer
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
    "WorkflowFileInput",
    "WorkflowFileArrayInput",
    "WorkflowDirectoryInput",
    "WorkflowDirectoryArrayInput",
    "WorkflowServiceUrlInput",
    "WorkflowConfigInput",
    "WorkflowSecretInput",
    # Workflow definition model
    "WorkflowDefinition",
]


class FrozenBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class WorkflowBaseInput(FrozenBaseModel):
    id: str
    required: bool = True
    type: str
    help: str = ""  # Help text to render alongside fields in GUI forms.


class WorkflowInjectedInput(WorkflowBaseInput):
    injected: Literal[True] = True


class WorkflowStringInput(WorkflowBaseInput):
    type: Literal["string"] = "string"


class WorkflowStringArrayInput(WorkflowBaseInput):
    type: Literal["string[]"] = "string[]"


class WorkflowNumberInput(WorkflowBaseInput):
    type: Literal["number"] = "number"


class WorkflowNumberArrayInput(WorkflowBaseInput):
    type: Literal["number[]"] = "number[]"


class WorkflowBooleanInput(WorkflowBaseInput):
    type: Literal["boolean"] = "boolean"


class WorkflowEnumInput(WorkflowBaseInput):
    type: Literal["enum"] = "enum"
    values: list[str] | str  # list of values, or a URL returning an array of enum values


class WorkflowEnumArrayInput(WorkflowBaseInput):
    type: Literal["enum[]"] = "enum[]"
    values: list[str] | str  # list of values, or a URL returning an array of enum values
    repeatable: bool = True


class WorkflowProjectDatasetInput(WorkflowBaseInput):
    type: Literal["project:dataset"] = "project:dataset"


class WorkflowFileInput(WorkflowBaseInput):
    # can be sourced from drop box / DRS / workflow outputs, whatever the UI decides works
    type: Literal["file"] = "file"
    pattern: str = ".+"  # file name regular expression pattern


class WorkflowFileArrayInput(WorkflowBaseInput):
    # can be sourced from drop box / DRS / workflow outputs, whatever the UI decides works
    type: Literal["file[]"] = "file[]"
    pattern: str = ".+"  # file name regular expression pattern


class WorkflowDirectoryInput(WorkflowBaseInput):
    # can be sourced from drop box / DRS / workflow outputs, whatever the UI decides works
    type: Literal["directory"] = "directory"


class WorkflowDirectoryArrayInput(WorkflowBaseInput):
    # can be sourced from drop box / DRS / workflow outputs, whatever the UI decides works
    type: Literal["directory[]"] = "directory[]"


class WorkflowServiceUrlInput(WorkflowInjectedInput):
    # service URL from the service registry, using bento.serviceKind as a lookup
    type: Literal["service-url"] = "service-url"
    service_kind: str


class WorkflowConfigInput(WorkflowInjectedInput):
    # configuration injection from the workflow executor - stored in the database
    type: Literal["config"] = "config"
    key: str


class WorkflowSecretInput(WorkflowInjectedInput):
    # secret injection from the workflow executor - not present in the database, passed ephemerally
    type: Literal["secret"] = "secret"
    key: str


WorkflowInput = (
    WorkflowStringInput
    | WorkflowStringArrayInput
    | WorkflowNumberInput
    | WorkflowNumberArrayInput
    | WorkflowBooleanInput
    | WorkflowEnumInput
    | WorkflowEnumArrayInput
    | WorkflowProjectDatasetInput
    | WorkflowFileInput
    | WorkflowFileArrayInput
    | WorkflowDirectoryInput
    | WorkflowDirectoryArrayInput
    | WorkflowServiceUrlInput
    | WorkflowConfigInput
    | WorkflowSecretInput
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
    data_type: str | None = None  # Data type; temporary for authz until we have proper token exchange for WES  TODO
    #  - If data_type is None, the permissions should be *more* severe, not less
    #    (check if they have whole project/dataset access)
    tags: frozenset[str] = frozenset()  # Should include data type(s) if relevant
    # Here, inputs defines UI / injected inputs for this workflow. These get transformed into a JSON parameters file
    # which is fed to the WDL workflow description / Cromwell.
    # As such, many of these workflow input types end up mapping to the same WDL type:
    #  - ex. the Bento WorkflowInput types enum/project:datraset/dataset/ref-genome all map to the WDL type String.
    inputs: list[WorkflowInput]

    @field_serializer("tags")
    def serialize_permissions(self, tags: frozenset[str], _info):
        # make set serialization have a consistent order
        return sorted(tags)
