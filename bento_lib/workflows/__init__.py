import os
import werkzeug.utils

from typing import Dict, List, Optional, Union

__all__ = [
    "WORKFLOW_TYPE_FILE",
    "WORKFLOW_TYPE_FILE_ARRAY",
    "WORKFLOW_TYPE_STRING",
    "WORKFLOW_TYPE_STRING_ARRAY",
    "WORKFLOW_TYPE_ENUM",
    "WORKFLOW_TYPE_ENUM_ARRAY",
    "WORKFLOW_TYPES",
    "WORKFLOW_FILE_TYPES",

    "file_with_prefix",
    "formatted_output",
    "namespaced_input",
    "make_output_params",
    "find_common_prefix",

    "secure_filename",
    "workflow_exists",
    "get_workflow",
    "get_workflow_resource",
]


WORKFLOW_TYPE_ARRAY_SUFFIX = "[]"


def array_of_type(workflow_type: str) -> str:
    return f"{workflow_type}{WORKFLOW_TYPE_ARRAY_SUFFIX}"


WORKFLOW_TYPE_FILE = "file"
WORKFLOW_TYPE_FILE_ARRAY = array_of_type(WORKFLOW_TYPE_FILE)
WORKFLOW_TYPE_STRING = "string"
WORKFLOW_TYPE_STRING_ARRAY = array_of_type("string")
WORKFLOW_TYPE_ENUM = "enum"
WORKFLOW_TYPE_ENUM_ARRAY = array_of_type("enum")

WORKFLOW_TYPES = frozenset((
    WORKFLOW_TYPE_FILE,
    WORKFLOW_TYPE_FILE_ARRAY,
    WORKFLOW_TYPE_STRING,
    WORKFLOW_TYPE_STRING_ARRAY,
    WORKFLOW_TYPE_ENUM,
    WORKFLOW_TYPE_ENUM_ARRAY,
))

WORKFLOW_FILE_TYPES = frozenset((WORKFLOW_TYPE_FILE, WORKFLOW_TYPE_FILE_ARRAY))


def file_with_prefix(file_name: str, prefix: Optional[int]) -> str:
    return f"{prefix}_{file_name}" if prefix is not None else file_name


def _output_file_name(file_name, output_params) -> Optional[str]:
    try:
        return secure_filename(file_name.format(**output_params))
    except KeyError:
        return None


def _output_file_name_array(file_template, map_from_input, output_params) -> Optional[List[str]]:
    try:
        return [secure_filename(file_template.format(v)) for v in output_params[map_from_input]]
    except KeyError:
        return None


def _output_string(string, output_params) -> Optional[str]:
    try:
        return string.format(**output_params)
    except KeyError:
        return None


def _output_string_array(string_template, map_from_input, output_params) -> Optional[List[str]]:
    try:
        return [string_template.format(v) for v in output_params[map_from_input]]
    except KeyError:
        return None


def formatted_output(output: dict, output_params: dict) -> Optional[Union[str, List[str]]]:
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


def make_output_params(workflow_id: str, workflow_params: dict, workflow_inputs: list) \
        -> Dict[str, Union[str, List[str]]]:
    # TODO: This can raise KeyError on os.path.basename(workflow_params[ni]) if ni is incorrect (e.g. missing the
    #  namespaced prefix.) This should be explicitly documented and perhaps ParameterException or something should be
    #  introduced to force custom handling for this exception.

    output_params = {}

    for i, input_spec in enumerate(workflow_inputs):
        if input_spec["type"] not in WORKFLOW_TYPES:
            raise NotImplementedError

        ni = namespaced_input(workflow_id, input_spec["id"])

        # If the input is not required and nothing was specified for it, skip it
        if not input_spec.get("required", True) and workflow_params.get(ni) is None:
            continue

        if input_spec["type"] in WORKFLOW_FILE_TYPES:
            # TODO: DOCS: Just file name without path...
            # TODO: Separate params for full path / path without drop_box stuff?

            output_params[input_spec["id"]] = ([os.path.basename(f) for f in workflow_params[ni]]
                                               if input_spec["type"].endswith(WORKFLOW_TYPE_ARRAY_SUFFIX)
                                               else os.path.basename(workflow_params[ni]))

        else:  # Primitive type or array of primitive type
            output_params[input_spec["id"]] = workflow_params[ni]

    return output_params


def _get_file_paths_from_output(base_path, output, output_params, prefix=None):
    fo = formatted_output(output, output_params)
    return (os.path.join(base_path, file_with_prefix(f, prefix)) for f in (fo if isinstance(fo, list) else [fo])
            if f is not None)


def find_common_prefix(base_path: str, workflow_metadata: dict, output_params: dict) -> Optional[int]:
    # Increase the prefix until a suitable one has been found, if needed

    prefix = None

    while True:
        duplicate_exists = False

        for output in workflow_metadata["outputs"]:
            # It only makes sense to deal with file outputs TODO: IS THIS TRUE?
            if output["type"] not in WORKFLOW_FILE_TYPES:
                continue

            duplicate_exists = duplicate_exists or any(
                os.path.exists(file_path)
                for file_path in _get_file_paths_from_output(
                    base_path, output, output_params, prefix))

            if duplicate_exists:
                # We already know this prefix isn't good enough, so stop
                # checking files until the next go-around.
                break

        if not duplicate_exists:
            # We've found a good prefix, exit the loop and the function
            return prefix

        # Otherwise, go around again to test a better prefix
        prefix = (prefix or 0) + 1


def secure_filename(fn: str) -> str:
    return werkzeug.utils.secure_filename(fn)


def workflow_exists(workflow_id: str, wfs: Dict):
    for key in wfs:
        if workflow_id in wfs[key]:
            return True

    return False


def get_workflow(workflow_id: str, wfs: Dict):
    for key in wfs:
        if workflow_id in wfs[key]:
            return wfs[key][workflow_id]

    raise KeyError(f'Workflow ID {workflow_id} not found.')


def get_workflow_resource(workflow_id: str, wfs: Dict):
    return secure_filename(get_workflow(workflow_id, wfs)["file"])
