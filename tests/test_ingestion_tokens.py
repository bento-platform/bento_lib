from datetime import datetime, timedelta

from bento_lib.ingestion import IngestionTokenManager

# TODO: Redis testing


def test_valid_tokens():
    tm = IngestionTokenManager("bento_lib")

    # Check valid token behaviour

    token = tm.generate_token()
    assert isinstance(token, str)
    assert tm.check_and_consume_token(token)


def test_invalid_tokens():
    tm = IngestionTokenManager("bento_lib")

    # Non-existent
    assert not tm.check_and_consume_token("fake_token")

    # Expired
    token = tm.generate_token()
    assert isinstance(token, str)
    tm._token_registry[token] = datetime.now() - timedelta(seconds=1)
    assert not tm.check_and_consume_token(token)


def test_clearing_tokens():
    tm = IngestionTokenManager("bento_lib")
    token = tm.generate_token()
    tm.clear_all_tokens()
    assert not tm.check_and_consume_token(token)
