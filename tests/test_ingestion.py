import json
import os
import pytest

from chord_lib.ingestion import (
    file_with_prefix,
    find_common_prefix,
    formatted_output,
    make_output_params,
    namespaced_input,
)


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
    assert file_with_prefix("test.test", None) == "test.test"
    assert file_with_prefix("test.test", 1) == "1_test.test"


def test_formatted_file_output():
    assert formatted_output(TEST_OUTPUT_FILE, TEST_OUTPUT_PARAMS) == "a_test.vcf.gz"


def test_formatted_file_array_output():
    assert all(
        o == "{}.gz".format(i)
        for i, o in zip(TEST_OUTPUT_PARAMS_ARRAY["vcfs"],
                        formatted_output(TEST_OUTPUT_FILE_ARRAY, TEST_OUTPUT_PARAMS_ARRAY))
    )


def test_formatted_string_array_output():
    assert all(
        o == "{}.gz".format(i)
        for i, o in zip(TEST_OUTPUT_PARAMS_ARRAY["vcfs"],
                        formatted_output(TEST_OUTPUT_STRING_ARRAY, TEST_OUTPUT_PARAMS_ARRAY))
    )


def test_formatted_string_output():
    assert formatted_output(TEST_OUTPUT_STRING, TEST_OUTPUT_PARAMS) == "a test.vcf"


def test_formatted_enum_output():
    # TODO: Should enum check if it's in the possible values?
    assert formatted_output(TEST_OUTPUT_ENUM, TEST_OUTPUT_PARAMS) == "a test.vcf"


def test_formatted_output_not_implemented():
    with pytest.raises(NotImplementedError):
        assert formatted_output({"type": "integer"}, TEST_OUTPUT_PARAMS)


def test_namespaced_input():
    assert namespaced_input("workflow1", "input") == "workflow1.input"


def test_make_output_params():
    output_params = make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_FILE])
    assert isinstance(output_params, dict)
    assert "vcf" in output_params
    assert len(list(output_params.keys())) == 1
    assert output_params["vcf"] == "does_not_exist.vcf"

    output_params = make_output_params("test", TEST_WORKFLOW_PARAMS_ARRAY, [TEST_INPUT_FILE_ARRAY])
    assert "vcfs" in output_params
    assert len(list(output_params.keys())) == 1
    assert json.dumps(output_params["vcfs"]) == json.dumps(["test1.vcf", "test2.vcf"])

    output_params = make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_STRING])
    assert "vcf" in output_params
    assert len(list(output_params.keys())) == 1
    assert output_params["vcf"] == TEST_WORKFLOW_PARAMS["test.vcf"]

    output_params = make_output_params("test", TEST_WORKFLOW_PARAMS_ARRAY, [TEST_INPUT_STRING_ARRAY])
    assert "vcfs" in output_params
    assert len(list(output_params.keys())) == 1
    assert json.dumps(output_params["vcfs"]) == json.dumps(["/tmp/test1.vcf", "/tmp/test2.vcf"])

    with pytest.raises(NotImplementedError):
        make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_DOES_NOT_EXIST])

    output_params = make_output_params("test", TEST_WORKFLOW_PARAMS, [])
    assert len(list(output_params.keys())) == 0


def test_find_common_prefix():
    output_params_1 = make_output_params("test", TEST_WORKFLOW_PARAMS, [TEST_INPUT_FILE])
    prefix_1 = find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_FILE]}, output_params_1)
    assert prefix_1 is None

    output_params_2 = make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING, [TEST_INPUT_FILE])
    prefix_2 = find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_STRING_EXISTING, TEST_OUTPUT_FILE_EXISTING]},
                                  output_params_2)
    assert prefix_2 == 1

    output_params_3 = make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING, [TEST_INPUT_FILE])
    prefix_3 = find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_FILE_EXISTING]}, output_params_3)
    assert prefix_3 == 1

    output_params_4 = make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING_2, [TEST_INPUT_FILE])
    prefix_4 = find_common_prefix(TEST_DATA_PATH, {"outputs": [TEST_OUTPUT_FILE_EXISTING]}, output_params_4)
    assert prefix_4 == 3

    output_params = make_output_params("test", TEST_WORKFLOW_PARAMS_EXISTING_3, [
        TEST_INPUT_FILE_ARRAY,
        TEST_INPUT_FILE_ARRAY_2,
    ])
    prefix = find_common_prefix(TEST_DATA_PATH, {"outputs": [
        TEST_OUTPUT_FILE_ARRAY_EXISTING,
        TEST_OUTPUT_FILE_ARRAY_EXISTING_2,
    ]}, output_params)
    assert prefix == 3
