import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from bento_lib.i18n.typing import EN, FR, TRANSLATED_STRING_ADAPTER, TranslatedString

HELLO: TranslatedString = {EN: "hello", FR: "bonjour"}


def test_translated_string_type_validate():
    ta = TypeAdapter(TranslatedString)

    assert ta.validate_python("hello") == "hello"
    assert ta.validate_python(HELLO) == HELLO

    with pytest.raises(ValidationError):
        ta.validate_python({})


TRANSLATED_STRING_SERIALIZATION_CASES: list[tuple[dict | None, bytes]] = [
    (None, b'{"en":"hello","fr":"bonjour"}'),
    ({"lang": "en"}, b'"hello"'),
    ({"lang": "fr"}, b'"bonjour"'),
    ({"lang": "es"}, b'"hello"'),  # language not found, use default policy (first)
    (
        {"lang": "es", "lang_fallback_policy": "first"},
        b'"hello"',
    ),  # language not found, use first policy explicitly
    # language not found, use non-default policy (blank):
    ({"lang": "es", "lang_fallback_policy": "blank"}, b'""'),
    # language not found, fallback to english:
    ({"lang": "es", "lang_fallback": ("en",)}, b'"hello"'),
    ({"lang": "es", "lang_fallback": ("zh", "en")}, b'"hello"'),
    # language not found, fallback to french:
    ({"lang": "es", "lang_fallback": ("fr",)}, b'"bonjour"'),
    ({"lang": "es", "lang_fallback": ("zh", "fr")}, b'"bonjour"'),
    # language not found, fallback to policy (first <-> English here):
    ({"lang": "es", "lang_fallback": ("zh",), "lang_fallback_policy": "first"}, b'"hello"'),
    # language not found, fallback to policy (blank):
    ({"lang": "es", "lang_fallback": ("zh",), "lang_fallback_policy": "blank"}, b'""'),
]


@pytest.mark.parametrize("context, result", TRANSLATED_STRING_SERIALIZATION_CASES)
def test_translated_string_type_serialize(context: dict | None, result: bytes):
    assert TRANSLATED_STRING_ADAPTER.dump_json(HELLO, context=context) == result


class TestModel(BaseModel):
    s1: TranslatedString
    s2: TranslatedString


INST = TestModel(s1="simple", s2=HELLO)


@pytest.mark.parametrize(
    "context, result",
    [
        (None, {"s1": "simple", "s2": HELLO}),
        ({"lang": "en"}, {"s1": "simple", "s2": "hello"}),
        ({"lang": "fr"}, {"s1": "simple", "s2": "bonjour"}),
        ({"lang": "es"}, {"s1": "simple", "s2": "hello"}),  # first
        ({"lang": "es", "lang_fallback_policy": "blank"}, {"s1": "simple", "s2": ""}),  # blank fallback
    ],
)
def test_translated_string_type_in_context(context: dict | None, result: dict):
    assert INST.model_dump(mode="json", context=context) == result
