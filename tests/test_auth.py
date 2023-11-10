import json

import pytest
from bento_lib.auth.permissions import (
    Permission,
    PermissionDefinitionError,
    QUERY_VERB,
    DATA,
    P_QUERY_PROJECT_LEVEL_BOOLEAN,
    P_QUERY_PROJECT_LEVEL_COUNTS,
    P_QUERY_DATA,
    P_DELETE_DATA,
)
from bento_lib.auth.resources import RESOURCE_EVERYTHING, build_resource


def test_recreate_permission_error():
    with pytest.raises(PermissionDefinitionError):
        Permission(QUERY_VERB, DATA)  # already exists


def test_permissions_equality():
    assert P_QUERY_DATA == P_QUERY_DATA
    assert P_QUERY_DATA == "query:data"
    assert P_QUERY_DATA != P_DELETE_DATA
    assert P_QUERY_DATA != "a"
    assert P_QUERY_DATA != 5


def test_permissions_repr():
    assert repr(P_QUERY_DATA) == "Permission(query:data)"


def test_permissions_hash():
    assert len({P_QUERY_DATA, P_QUERY_DATA, P_DELETE_DATA}) == 2


def test_permissions_gives():
    assert P_QUERY_PROJECT_LEVEL_BOOLEAN in P_QUERY_PROJECT_LEVEL_COUNTS.gives

    assert P_QUERY_PROJECT_LEVEL_BOOLEAN in P_QUERY_DATA.gives
    assert P_QUERY_PROJECT_LEVEL_COUNTS in P_QUERY_DATA.gives

    assert P_QUERY_DATA not in P_QUERY_PROJECT_LEVEL_COUNTS.gives


def test_build_resource():
    assert build_resource() == RESOURCE_EVERYTHING
    assert json.dumps(build_resource(project="a")) == json.dumps({"project": "a"})
    assert json.dumps(build_resource(project="a", data_type="z"), sort_keys=True) == json.dumps(
        {"data_type": "z", "project": "a"}, sort_keys=True)
    assert json.dumps(build_resource(project="a", dataset="z"), sort_keys=True) == json.dumps(
        {"dataset": "z", "project": "a"}, sort_keys=True)
    assert json.dumps(build_resource(project="a", dataset="z", data_type="t"), sort_keys=True) == json.dumps(
        {"data_type": "t", "dataset": "z", "project": "a"}, sort_keys=True)
