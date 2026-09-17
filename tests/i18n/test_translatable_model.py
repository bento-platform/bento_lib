from __future__ import annotations

import json

from bento_lib.i18n import (
    EN,
    ES,
    FR,
    TranslatableModel,
)


class TestTranslatableModel:
    def test_default_language_is_en(self):
        class M(TranslatableModel):
            pass

        m = M()
        assert m.language == EN

    def test_model_dump_injects_lang(self, access_level):
        class M(TranslatableModel):
            level: access_level  # type: ignore

        m = M(level="Open", language=FR)
        dumped = m.model_dump()
        assert dumped["level"] == "Ouvert"

    def test_model_dump_json_injects_lang(self, access_level):
        class M(TranslatableModel):
            level: access_level  # type: ignore

        m = M(level="Embargoed", language=ES)
        raw = m.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["level"] == "Embargado"

    def test_model_dump_en_default(self, access_level):
        class M(TranslatableModel):
            level: access_level  # type: ignore

        m = M(level="Open")
        dumped = m.model_dump()
        assert dumped["level"] == "Open"

    def test_model_dump_preserves_existing_context(self, access_level):
        class M(TranslatableModel):
            level: access_level  # type: ignore

        m = M(level="Open", language=FR)
        dumped = m.model_dump(context={"extra": "value"})
        assert dumped["level"] == "Ouvert"

    def test_inject_lang_context_no_existing_context(self):
        m = TranslatableModel(language=FR)
        kwargs = {}
        result = m._inject_lang_context(kwargs)
        assert result["context"]["lang"] == FR

    def test_inject_lang_context_existing_context(self):
        m = TranslatableModel(language=ES)
        kwargs = {"context": {"foo": "bar"}}
        result = m._inject_lang_context(kwargs)
        assert result["context"]["lang"] == ES
        assert result["context"]["foo"] == "bar"
