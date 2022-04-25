import json
import os
import pytest
import werkzeug.utils

from bento_lib import workflows

TEST_WORKFLOWS = {
    "ingestion": {
        "test": {
            "file": "test.wdl"
        }
    },
    "analysis": {
        "test_analysis": {
            "file": "../../../test analysis.wdl"
        }
    },
    "export": {
        "test_export": {
            "file": "test_export.wdl"
        }
    }
}


TEST_OUTPUT_PARAMS = {
    "vcf": "test.vcf"
}

TEST_OUTPUT_PARAMS_ARRAY = {
    "vcfs": ["test.vcf", "test2.vcf"]
}

TEST_OUTPUT_FILE = {
    "id": "vcf_gz",
    "type": "file",
    "value": "a {vcf}.gz"
}

TEST_OUTPUT_FILE_ARRAY = {
    "id": "vcf_gz",
    "type": "file[]",
    "map_from_input": "vcfs",
    "value": "{}.gz"
}

TEST_OUTPUT_STRING = {
    "id": "vcf_gz",
    "type": "string",
    "value": "a {vcf}"
}

TEST_OUTPUT_STRING_ARRAY = {
    "id": "vcf_gz",
    "type": "string[]",
    "map_from_input": "vcfs",
    "value": "{}.gz"
}

TEST_OUTPUT_ENUM = {
    "id": "vcf_gz",
    "type": "enum",
    "value": "a {vcf}"
}

TEST_WORKFLOW_PARAMS = {
    "test.vcf": "/tmp/does_not_exist.vcf"
}

TEST_WORKFLOW_PARAMS_ARRAY = {
    "test.vcfs": ["/tmp/test1.vcf", "/tmp/test2.vcf"]
}

TEST_INPUT_FILE = {
    "id": "vcf",
    "type": "file"
}

TEST_INPUT_FILE_ARRAY = {
    "id": "vcfs",
    "type": "file[]"
}

TEST_INPUT_FILE_ARRAY_2 = {
    "id": "vcfs_2",
    "type": "file[]"
}

TEST_INPUT_STRING = {
    "id": "vcf",
    "type": "string"
}

TEST_INPUT_STRING_ARRAY = {
    "id": "vcfs",
    "type": "string[]"
}

TEST_INPUT_DOES_NOT_EXIST = {
    "id": "vcfs",
    "type": "does_not_exist"
}


TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

TEST_WORKFLOW_PARAMS_EXISTING = {
    "test.vcf": os.path.join(TEST_DATA_PATH, "existing.txt")
}

TEST_OUTPUT_FILE_EXISTING = {
    "id": "vcf_out",
    "type": "file",
    "value": "{vcf}"
}

TEST_OUTPUT_STRING_EXISTING = {
    "id": "vcf_out_2",
    "type": "string",
    "value": "{vcf}"
}

TEST_WORKFLOW_PARAMS_EXISTING_2 = {
    "test.vcf": os.path.join(TEST_DATA_PATH, "dup.txt")
}

TEST_WORKFLOW_PARAMS_EXISTING_3 = {
    "test.vcfs": [
        os.path.join(TEST_DATA_PATH, "a.txt"),
        os.path.join(TEST_DATA_PATH, "b.txt"),
    ],
    "test.vcfs_2": [
        os.path.join(TEST_DATA_PATH, "c.txt"),
    ]
}

TEST_OUTPUT_FILE_ARRAY_EXISTING = {
    "id": "vcfs_out",
    "type": "file[]",
    "map_from_input": "vcfs",
    "value": "{}"
}

TEST_OUTPUT_FILE_ARRAY_EXISTING_2 = {
    "id": "vcfs_out_2",
    "type": "file[]",
    "map_from_input": "vcfs_2",
    "value": "{}"
}


def test_file_with_prefix():
    assert workflows.file_with_prefix("test.test", None) == "test.test"
    assert workflows.file_with_prefix("test.test", 1) == "1_test.test"


def test_formatted_file_output():
    assert workflows.formatted_output(TEST_OUTPUT_FILE, TEST_OUTPUT_PARAMS) == "a_test.vcf.gz"


def test_formatted_file_array_output():
    assert all(
        o == "{}.gz".format(i)
        for i, o in zip(TEST_OUTPUT_PARAMS_ARRAY["vcfs"],
                        workflows.formatted_output(TEST_OUTPUT_FILE_ARRAY, TEST_OUTPUT_PARAMS_ARRAY))
    )


def test_formatted_string_array_output():
    assert all(
        o == "{}.gz".format(i)
        for i, o in zip(TEST_OUTPUT_PARAMS_ARRAY["vcfs"],
                        workflows.formatted_output(TEST_OUTPUT_STRING_ARRAY, TEST_OUTPUT_PARAMS_ARRAY))
    )


def test_formatted_string_output():
    assert workflows.formatted_output(TEST_OUTPUT_STRING, TEST_OUTPUT_PARAMS) == "a test.vcf"


def test_formatted_enum_output():
    # TODO: Should enum check if it's in the possible values?
    assert workflows.formatted_output(TEST_OUTPUT_ENUM, TEST_OUTPUT_PARAMS) == "a test.vcf"


def test_formatted_output_not_implemented():
    with pytest.raises(NotImplementedError):
        assert workflows.formatted_output({"type": "integer"}, TEST_OUTPUT_PARAMS)


def test_namespaced_input():
    assert workflows.namespaced_input("workflow1", "input") == "workflow1.input"


def test_make_output_params():
    output_params = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_FILE])
    assert isinstance(output_params, dict)
    assert "vcf" in output_params
    assert len(list(output_params.keys())) == 1
    assert output_params["vcf"] == "does_not_exist.vcf"

    output_params = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS_ARRAY, [TEST_INPUT_FILE_ARRAY])
    assert "vcfs" in output_params
    assert len(list(output_params.keys())) == 1
    assert json.dumps(output_params["vcfs"]) == json.dumps(["test1.vcf", "test2.vcf"])

    output_params = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_STRING])
    assert "vcf" in output_params
    assert len(list(output_params.keys())) == 1
    assert output_params["vcf"] == TEST_WORKFLOW_PARAMS["test.vcf"]

    output_params = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS_ARRAY, [TEST_INPUT_STRING_ARRAY])
    assert "vcfs" in output_params
    assert len(list(output_params.keys())) == 1
    assert json.dumps(output_params["vcfs"]) == json.dumps(["/tmp/test1.vcf", "/tmp/test2.vcf"])

    with pytest.raises(NotImplementedError):
        workflows.make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_DOES_NOT_EXIST])

    output_params = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS, [])
    assert len(list(output_params.keys())) == 0


def test_optional_inputs():
    for ip in (TEST_INPUT_FILE, TEST_INPUT_FILE_ARRAY, TEST_INPUT_STRING, TEST_INPUT_STRING_ARRAY):
        output_params = workflows.make_output_params("test", {}, [{**ip, "required": False}])
        assert json.dumps(output_params) == "{}"


def test_optional_input_formatting():
    assert workflows.formatted_output(TEST_OUTPUT_FILE, {}) is None
    assert workflows.formatted_output(TEST_OUTPUT_FILE_ARRAY, {}) is None
    assert workflows.formatted_output(TEST_OUTPUT_STRING, {}) is None
    assert workflows.formatted_output(TEST_OUTPUT_STRING_ARRAY, {}) is None


def test_find_common_prefix():
    output_params_1 = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_FILE])
    prefix_1 = workflows.find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_FILE]}, output_params_1)
    assert prefix_1 is None

    output_params_2 = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING, [TEST_INPUT_FILE])
    prefix_2 = workflows.find_common_prefix(
        TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_STRING_EXISTING, TEST_OUTPUT_FILE_EXISTING]}, output_params_2)
    assert prefix_2 == 1

    output_params_3 = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING, [TEST_INPUT_FILE])
    prefix_3 = workflows.find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_FILE_EXISTING]}, output_params_3)
    assert prefix_3 == 1

    output_params_4 = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING_2, [TEST_INPUT_FILE])
    prefix_4 = workflows.find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_FILE_EXISTING]}, output_params_4)
    assert prefix_4 == 3

    output_params = workflows.make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING_3, [
        TEST_INPUT_FILE_ARRAY,
        TEST_INPUT_FILE_ARRAY_2,
    ])
    prefix = workflows.find_common_prefix(TEST_DATA_PATH, {"outputs": [
        TEST_OUTPUT_FILE_ARRAY_EXISTING,
        TEST_OUTPUT_FILE_ARRAY_EXISTING_2,
    ]}, output_params)
    assert prefix == 3


def test_secure_filename():
    assert workflows.secure_filename("../../test file.exe") == werkzeug.utils.secure_filename("../../test file.exe")


def test_workflow_exists():
    assert workflows.workflow_exists("test", TEST_WORKFLOWS)
    assert workflows.workflow_exists("test_analysis", TEST_WORKFLOWS)
    assert workflows.workflow_exists("test_export", TEST_WORKFLOWS)
    assert not workflows.workflow_exists("does_not_exist", TEST_WORKFLOWS)


def test_get_workflow():
    assert workflows.get_workflow("test", TEST_WORKFLOWS) == TEST_WORKFLOWS["ingestion"]["test"]
    assert workflows.get_workflow("test_analysis", TEST_WORKFLOWS) == TEST_WORKFLOWS["analysis"]["test_analysis"]
    assert workflows.get_workflow("test_export", TEST_WORKFLOWS) == TEST_WORKFLOWS["export"]["test_export"]
    with pytest.raises(KeyError):
        workflows.get_workflow("does_not_exist", TEST_WORKFLOWS)


def test_get_workflow_resource():
    assert workflows.get_workflow_resource("test", TEST_WORKFLOWS) == "test.wdl"
    assert workflows.get_workflow_resource("test_analysis", TEST_WORKFLOWS) == "test_analysis.wdl"
    assert workflows.get_workflow_resource("test_export", TEST_WORKFLOWS) == "test_export.wdl"
    with pytest.raises(KeyError):
        workflows.get_workflow_resource("does_not_exist", TEST_WORKFLOWS)
