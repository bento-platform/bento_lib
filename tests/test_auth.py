import pytest
from bento_lib.auth.permissions import (
    Permission,
    PermissionDefinitionError,
    QUERY_VERB,
    DATA,
    P_QUERY_DATA,
    P_DELETE_DATA,
)


def test_recreate_permission_error():
    with pytest.raises(PermissionDefinitionError):
        Permission(QUERY_VERB, DATA)  # already exists


def test_equality():
    assert P_QUERY_DATA == P_QUERY_DATA
    assert P_QUERY_DATA == "query:data"
    assert P_QUERY_DATA != P_DELETE_DATA
    assert P_QUERY_DATA != "a"
    assert P_QUERY_DATA != 5


def test_repr():
    assert repr(P_QUERY_DATA) == "Permission(query:data)"


def test_hash():
    assert len({P_QUERY_DATA, P_QUERY_DATA, P_DELETE_DATA}) == 2
