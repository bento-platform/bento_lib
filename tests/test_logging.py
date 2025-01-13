import logging
from bento_lib.logging import log_level_from_str
from bento_lib.logging.structured import configure as struct_config


def test_log_level_from_str():
    assert log_level_from_str("DEBUG") == logging.DEBUG
    assert log_level_from_str("info") == logging.INFO
    assert log_level_from_str("asdf", default=logging.DEBUG) == logging.DEBUG
    assert log_level_from_str("asdf", default=logging.INFO) == logging.INFO


def test_drop_color_message():
    assert struct_config.drop_color_message_key(
        None,
        None,
        {"color_message": "Hello with style", "message": "Hello"},
    ) == {"message": "Hello"}

    assert struct_config.drop_color_message_key(None, None, {"message": "hi"}) == {"message": "hi"}


def test_build_handler():
    # lame duck test to at least ensure this function works
    assert isinstance(struct_config._build_root_logger_handler(False), logging.StreamHandler)
    assert isinstance(struct_config._build_root_logger_handler(True), logging.StreamHandler)
