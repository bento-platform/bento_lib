from bento_lib.utils.operators import is_not_none


def test_utils_operators_is_not_none():
    assert is_not_none(5)
    assert is_not_none("true")
    assert not is_not_none(None)
