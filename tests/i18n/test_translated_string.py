import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from bento_lib.i18n.typing import EN, FR, TranslatedString

HELLO: TranslatedString = {EN: "hello", FR: "bonjour"}


def test_translated_string_type():
    ta = TypeAdapter(TranslatedString)

    assert ta.validate_python("hello") == "hello"
    assert ta.validate_python(HELLO) == HELLO

    assert ta.dump_json(HELLO) == b'{"en":"hello","fr":"bonjour"}'
    assert ta.dump_json(HELLO, context={"translate": True}) == b'"hello"'
    assert ta.dump_json(HELLO, context={"lang": "fr"}) == b'"bonjour"'  # translate implicitly True
    assert ta.dump_json(HELLO, context={"lang": "es", "translate": True}) == b'"hello"'  # language not found

    with pytest.raises(ValidationError):
        ta.validate_python({})


def test_translated_string_type_in_context():
    class TestModel(BaseModel):
        s1: TranslatedString
        s2: TranslatedString

    inst = TestModel(s1="simple", s2=HELLO)
    assert inst.model_dump(mode="json") == {"s1": "simple", "s2": HELLO}
    assert inst.model_dump(mode="json", context={"translate": True}) == {"s1": "simple", "s2": "hello"}
    assert inst.model_dump(mode="json", context={"lang": "fr"}) == {"s1": "simple", "s2": "bonjour"}
