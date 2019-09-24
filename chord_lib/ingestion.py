import os

from typing import Optional
from werkzeug.utils import secure_filename


__all__ = [
    "WORKFLOW_TYPE_FILE",
    "WORKFLOW_TYPE_STRING",
    "WORKFLOW_TYPE_ENUM",

    "file_with_prefix",
    "formatted_output",
    "namespaced_input",
    "make_output_params",
    "find_common_prefix",
]


WORKFLOW_TYPE_FILE = "file"
WORKFLOW_TYPE_STRING = "string"
WORKFLOW_TYPE_ENUM = "enum"


def file_with_prefix(file_path: str, prefix: int) -> str:
    file_parts = os.path.splitext(file_path)
    return "".join(("{}_{}".format(prefix, file_parts[0]), file_parts[1]))


def _output_file_name(file_name, output_params):
    return secure_filename(file_name.format(**output_params))


def _output_string(string, output_params):
    return string.format(**output_params)


def formatted_output(output: dict, output_params: dict):
    if output["type"] == WORKFLOW_TYPE_FILE:
        return _output_file_name(output["value"], output_params)
    elif output["type"] in (WORKFLOW_TYPE_STRING, WORKFLOW_TYPE_ENUM):  # TODO: Check enum values?
        return _output_string(output["value"], output_params)
    else:
        raise NotImplementedError


def namespaced_input(workflow_name: str, input_id: str) -> str:
    return "{}.{}".format(workflow_name, input_id)


def make_output_params(workflow_id: str, workflow_params: dict, workflow_inputs: list):
    output_params = {}

    for i, input_spec in enumerate(workflow_inputs):
        if input_spec["type"] != WORKFLOW_TYPE_FILE:
            # TODO: Handle non-file inputs
            continue

        # TODO: DOCS: Just file name without path...
        # TODO: Separate params for full path / path without drop_box stuff?

        output_params[input_spec["id"]] = os.path.basename(
            workflow_params[namespaced_input(workflow_id, input_spec["id"])])

    return output_params


def find_common_prefix(base_path: str, workflow_metadata: dict, output_params: dict) -> Optional[int]:
    prefix = None
    for output in workflow_metadata["outputs"]:
        # It only makes sense to deal with file outputs TODO: IS THIS TRUE?
        if output["type"] != WORKFLOW_TYPE_FILE:
            continue

        file_path = os.path.join(base_path, formatted_output(output, output_params))
        if os.path.exists(file_path):
            prefix = 1

    # Increase the prefix until a suitable one has been found
    duplicate_exists = prefix is not None
    while duplicate_exists:
        duplicate_exists = False

        for output in workflow_metadata["outputs"]:
            # It only makes sense to deal with file outputs TODO: IS THIS TRUE?
            if output["type"] != WORKFLOW_TYPE_FILE:
                continue

            duplicate_exists = duplicate_exists or os.path.exists(
                os.path.join(base_path, file_with_prefix(formatted_output(output, output_params), prefix)))

        if duplicate_exists:
            prefix += 1

    return prefix
