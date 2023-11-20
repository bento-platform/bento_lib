import logging
from bento_lib.logging import log_level_from_str


def test_log_level_from_str():
    assert log_level_from_str("DEBUG") == logging.DEBUG
    assert log_level_from_str("info") == logging.INFO
    assert log_level_from_str("asdf", default=logging.DEBUG) == logging.DEBUG
    assert log_level_from_str("asdf", default=logging.INFO) == logging.INFO
