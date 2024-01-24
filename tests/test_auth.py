import json

import pytest
from bento_lib.auth.helpers import permission_valid_for_resource, valid_permissions_for_resource
from bento_lib.auth.permissions import (
    Permission,
    PermissionDefinitionError,
    PERMISSIONS,
    LEVEL_INSTANCE,
    QUERY_VERB,
    DATA,
    P_QUERY_PROJECT_LEVEL_BOOLEAN,
    P_QUERY_PROJECT_LEVEL_COUNTS,
    P_QUERY_DATA,
    P_DELETE_DATA,
    P_VIEW_DROP_BOX,
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


def test_permissions_valid_for_resource():
    assert permission_valid_for_resource(P_QUERY_DATA, RESOURCE_EVERYTHING)
    assert permission_valid_for_resource(P_QUERY_DATA, {"project": "aaa"})
    assert permission_valid_for_resource(P_QUERY_DATA, {"project": "aaa", "dataset": "bbb"})

    # project and above
    assert permission_valid_for_resource(P_QUERY_PROJECT_LEVEL_BOOLEAN, RESOURCE_EVERYTHING)
    assert permission_valid_for_resource(P_QUERY_PROJECT_LEVEL_BOOLEAN, {"project": "aaa"})
    assert not permission_valid_for_resource(P_QUERY_PROJECT_LEVEL_BOOLEAN, {"project": "aaa", "dataset": "bbb"})

    # instance only
    assert permission_valid_for_resource(P_VIEW_DROP_BOX, RESOURCE_EVERYTHING)
    assert not permission_valid_for_resource(P_VIEW_DROP_BOX, {"project": "aaa"})
    assert not permission_valid_for_resource(P_VIEW_DROP_BOX, {"project": "aaa", "dataset": "bbb"})


def test_all_valid_permissions_for_resource():
    assert valid_permissions_for_resource(RESOURCE_EVERYTHING) == PERMISSIONS
    assert valid_permissions_for_resource({"project": "aaa"}) == [
        p for p in PERMISSIONS if p.min_level_required != LEVEL_INSTANCE]
