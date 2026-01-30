import pytest

from bento_lib.i18n import i18n_value


@pytest.mark.parametrize(
    "v, lang, result",
    (
        ("plain", "en", "plain"),
        ("plain", "fr", "plain"),
        ({"en": "hello", "fr": "bonjour"}, "en", "hello"),
        ({"en": "hello", "fr": "bonjour"}, "fr", "bonjour"),
        ({"en": "hello", "fr": "bonjour"}, "es", "hello"),
        ({"fr": "bonjour", "en": "hello"}, "es", "bonjour"),
    ),
)
def test_i18n_value(v, lang, result):
    assert i18n_value(v, lang) == result
