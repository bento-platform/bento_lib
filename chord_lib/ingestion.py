import os

from typing import Optional
from werkzeug.utils import secure_filename


__all__ = [
    "WORKFLOW_TYPE_FILE",
    "WORKFLOW_TYPE_FILE_ARRAY",
    "WORKFLOW_TYPE_STRING",
    "WORKFLOW_TYPE_STRING_ARRAY",
    "WORKFLOW_TYPE_ENUM",
    "WORKFLOW_TYPE_ENUM_ARRAY",

    "file_with_prefix",
    "formatted_output",
    "namespaced_input",
    "make_output_params",
    "find_common_prefix",
]


WORKFLOW_TYPE_ARRAY_SUFFIX = "[]"


def array_of_type(workflow_type: str):
    return "{}{}".format(workflow_type, WORKFLOW_TYPE_ARRAY_SUFFIX)


WORKFLOW_TYPE_FILE = "file"
WORKFLOW_TYPE_FILE_ARRAY = array_of_type(WORKFLOW_TYPE_FILE)
WORKFLOW_TYPE_STRING = "string"
WORKFLOW_TYPE_STRING_ARRAY = array_of_type("string")
WORKFLOW_TYPE_ENUM = "enum"
WORKFLOW_TYPE_ENUM_ARRAY = array_of_type("enum")

WORKFLOW_FILE_TYPES = {WORKFLOW_TYPE_FILE, WORKFLOW_TYPE_FILE_ARRAY}


def file_with_prefix(file_name: str, prefix: Optional[int]) -> str:
    return f"{prefix}_{file_name}" if prefix is not None else file_name


def _output_file_name(file_name, output_params):
    return secure_filename(file_name.format(**output_params))


def _output_file_name_array(file_template, map_from_input, output_params):
    return [secure_filename(file_template.format(v)) for v in output_params[map_from_input]]


def _output_string(string, output_params):
    return string.format(**output_params)


def _output_string_array(string_template, map_from_input, output_params):
    return [string_template.format(v) for v in output_params[map_from_input]]


def formatted_output(output: dict, output_params: dict):
    if output["type"] == WORKFLOW_TYPE_FILE:
        return _output_file_name(output["value"], output_params)
    elif output["type"] == WORKFLOW_TYPE_FILE_ARRAY:
        return _output_file_name_array(output["value"], output["map_from_input"], output_params)
    elif output["type"] in (WORKFLOW_TYPE_STRING, WORKFLOW_TYPE_ENUM):  # TODO: Check enum values?
        return _output_string(output["value"], output_params)
    elif output["type"] in (WORKFLOW_TYPE_STRING_ARRAY, WORKFLOW_TYPE_ENUM_ARRAY):
        return _output_string_array(output["value"], output["map_from_input"], output_params)
    else:
        raise NotImplementedError


def namespaced_input(workflow_name: str, input_id: str) -> str:
    return f"{workflow_name}.{input_id}"


def make_output_params(workflow_id: str, workflow_params: dict, workflow_inputs: list):
    output_params = {}

    for i, input_spec in enumerate(workflow_inputs):
        if input_spec["type"] in WORKFLOW_FILE_TYPES:
            # TODO: DOCS: Just file name without path...
            # TODO: Separate params for full path / path without drop_box stuff?

            ni = namespaced_input(workflow_id, input_spec["id"])
            output_params[input_spec["id"]] = ([os.path.basename(f) for f in workflow_params[ni]]
                                               if input_spec["type"].endswith(WORKFLOW_TYPE_ARRAY_SUFFIX)
                                               else os.path.basename(workflow_params[ni]))

        elif input_spec["type"] in (WORKFLOW_TYPE_STRING, WORKFLOW_TYPE_STRING_ARRAY, WORKFLOW_TYPE_ENUM,
                                    WORKFLOW_TYPE_ENUM_ARRAY):
            output_params[input_spec["id"]] = workflow_params[namespaced_input(workflow_id, input_spec["id"])]

        else:
            raise NotImplementedError

    return output_params


def _get_file_paths_from_output(base_path, output, output_params, prefix=None):
    fo = formatted_output(output, output_params)
    return (os.path.join(base_path, file_with_prefix(f, prefix)) for f in (fo if isinstance(fo, list) else [fo]))


def find_common_prefix(base_path: str, workflow_metadata: dict, output_params: dict) -> Optional[int]:
    # Increase the prefix until a suitable one has been found, if needed

    prefix = None

    while True:
        duplicate_exists = False

        for output in workflow_metadata["outputs"]:
            if duplicate_exists:
                break

            # It only makes sense to deal with file outputs TODO: IS THIS TRUE?
            if output["type"] not in WORKFLOW_FILE_TYPES:
                continue

            for file_path in _get_file_paths_from_output(base_path, output, output_params, prefix):
                duplicate_exists = duplicate_exists or os.path.exists(file_path)

        if duplicate_exists:
            prefix = prefix + 1 if prefix is not None else 1
            continue  # Go around again to find a better prefix

        break

    return prefix
