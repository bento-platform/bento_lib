import json
from datetime import datetime, timedelta

from bento_lib.ingestion import IngestionTokenManager


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
    tm._token_registry[token] = (datetime.now() - timedelta(seconds=1)).timestamp()
    assert not tm.check_and_consume_token(token)


def test_clearing_tokens():
    tm = IngestionTokenManager("bento_lib")
    token = tm.generate_token()
    tm.clear_all_tokens()
    assert not tm.check_and_consume_token(token)


def test_with_redis():
    # Start in Redis mode, using connection defaults
    tm = IngestionTokenManager("bento_lib", redis_connection_data={})
    assert tm._redis_key == "bento_lib_ingest_tokens"

    # Clear old test data
    tm.clear_all_tokens()

    token = tm.generate_token()
    redis_cache = tm._redis_fetch()

    assert token in redis_cache
    assert json.dumps(redis_cache, sort_keys=True) == json.dumps(tm._token_registry, sort_keys=True)

    assert tm.check_and_consume_token(token)
    redis_cache = tm._redis_fetch()
    assert json.dumps(redis_cache, sort_keys=True) == json.dumps({})

    tm.generate_token()
    tm.clear_all_tokens()
    redis_cache = tm._redis_fetch()
    assert json.dumps(redis_cache, sort_keys=True) == json.dumps({})

    # Check that a simulated connection hiccup is handled (i.e. the generated
    # token is available on re-connection)

    token = tm.generate_token()
    tm2 = IngestionTokenManager("bento_lib", redis_connection_data={})
    assert tm2.check_and_consume_token(token)
