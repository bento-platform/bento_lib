from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from ..auth.middleware.fastapi import FastApiAuthMiddleware
from .models import WorkflowDefinition
from .workflow_set import WorkflowSet

__all__ = [
    "build_workflow_router",
]


def build_workflow_router(authz_middleware: FastApiAuthMiddleware, workflow_set: WorkflowSet) -> APIRouter:
    workflow_router = APIRouter(prefix="/workflows")

    @workflow_router.get("", dependencies=[authz_middleware.dep_public_endpoint()])
    def workflow_list():
        return workflow_set.workflow_dicts_by_type_and_id()

    @workflow_router.get("/", dependencies=[authz_middleware.dep_public_endpoint()])
    def workflow_list_trailing_slash():
        return workflow_set.workflow_dicts_by_type_and_id()

    # The endpoint with the .wdl suffix needs to come first, since we match in order and otherwise the whole thing,
    # including the suffix, would get passed as {workflow_id}.
    @workflow_router.get("/{workflow_id}.wdl", dependencies=[authz_middleware.dep_public_endpoint()])
    def workflow_file(workflow_id: str):
        if (wdl := workflow_set.get_workflow_wdl_path(workflow_id)) is not None:
            return FileResponse(wdl)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No workflow with ID {workflow_id}")

    @workflow_router.get("/{workflow_id}", dependencies=[authz_middleware.dep_public_endpoint()])
    def workflow_item(workflow_id: str) -> WorkflowDefinition:
        if (wf := workflow_set.get_workflow(workflow_id)) is not None:
            return wf
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No workflow with ID {workflow_id}")

    return workflow_router
