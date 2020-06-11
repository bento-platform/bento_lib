import werkzeug.utils

from typing import Dict


def secure_filename(fn: str) -> str:
    return werkzeug.utils.secure_filename(fn)


def workflow_exists(workflow_id: str, wfs: Dict):
    return workflow_id in wfs["ingestion"] or workflow_id in wfs["analysis"]


def get_workflow(workflow_id: str, wfs: Dict):
    return (wfs["ingestion"][workflow_id] if workflow_id in wfs["ingestion"]
            else wfs["analysis"][workflow_id])


def get_workflow_resource(workflow_id: str, wfs: Dict):
    return secure_filename(get_workflow(workflow_id, wfs)["file"])
