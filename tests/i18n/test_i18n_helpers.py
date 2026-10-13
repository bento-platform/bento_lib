import json

import pytest
from test_translated_string import HELLO, TRANSLATED_STRING_SERIALIZATION_CASES

from bento_lib.i18n.helpers import render_translated_text


@pytest.mark.parametrize("context, result", TRANSLATED_STRING_SERIALIZATION_CASES)
def test_render_translated_text(context: dict | None, result: bytes):
    if context is None:
        return

    kwargs = {"fallback": context.get("lang_fallback", ())}
    if fallback_policy := context.get("lang_fallback_policy"):
        kwargs["policy"] = fallback_policy

    assert render_translated_text(HELLO, context["lang"], **kwargs) == json.loads(result)
