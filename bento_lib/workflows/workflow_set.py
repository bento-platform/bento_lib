import werkzeug.utils
from collections import defaultdict
from .models import WorkflowDefinition

__all__ = [
    "WorkflowSet",
]


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

    def get_workflow_resource(self, id_: str) -> str | None:
        if (wd := self.get_workflow(id_)) is not None:
            return werkzeug.utils.secure_filename(wd.file)
        return None

    def workflow_exists(self, id_: str) -> bool:
        return id_ in self._defs_by_id

    def workflow_dicts_by_type_and_id(self) -> dict[str, dict[str, dict]]:
        by_type = defaultdict(dict)
        for id_, wf in self._defs_by_id.items():
            by_type[wf.type][id_] = wf.model_dump(mode="json")
        return dict(by_type)

    def workflow_dicts_by_id(self) -> dict[str, WorkflowDefinition]:
        return {k: v.model_dump(mode="json") for k, v in self._defs_by_id.items()}
