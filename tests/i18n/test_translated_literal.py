from __future__ import annotations

import json
import pytest
from pydantic import BaseModel, ValidationError
from pydantic_extra_types.language_code import LanguageAlpha2

from bento_lib.i18n import (
    EN,
    ES,
    FR,
    TranslatedLiteral,
)



# ── TranslatedLiteral.__init__ ───────────────────────────────────────────

class TestTranslatedLiteralInit:
    def test_first_lang_must_be_en(self):
        with pytest.raises(ValueError, match="First language must be 'en'"):
            TranslatedLiteral(FR, EN)

    def test_empty_langs_raises(self):
        with pytest.raises(ValueError, match="First language must be 'en'"):
            TranslatedLiteral()

    def test_valid_init(self):
        tl = TranslatedLiteral(EN, FR)
        assert tl.langs == (EN, FR)


# ── TranslatedLiteral.__call__ ───────────────────────────────────────────

class TestTranslatedLiteralCall:
    def test_mismatched_term_length_raises(self):
        tl = TranslatedLiteral(EN, FR, ES)
        with pytest.raises(ValueError, match="has 2 values, expected 3"):
            tl(("Open", "Ouvert"))  # missing ES

    def test_returns_self(self):
        tl = TranslatedLiteral(EN, FR)
        result = tl(("Yes", "Oui"))
        assert result is tl

    def test_en_values_populated(self, access_level):
        assert access_level.en_values == {"Open", "Restricted", "Embargoed"}

    def test_translations_populated(self, access_level):
        assert access_level.translations["Open"] == {FR: "Ouvert", ES: "Abierto"}
        assert access_level.translations["Restricted"] == {FR: "Restreint", ES: "Restringido"}

    def test_to_en_reverse_lookup(self, access_level):
        assert access_level.to_en["Ouvert"] == "Open"
        assert access_level.to_en["Abierto"] == "Open"
        assert access_level.to_en["Open"] == "Open"  # EN maps to itself


# ── translate ─────────────────────────────────────────────────────────────

class TestTranslate:
    def test_translate_to_fr(self, access_level):
        assert access_level.translate("Open", FR) == "Ouvert"

    def test_translate_to_es(self, access_level):
        assert access_level.translate("Embargoed", ES) == "Embargado"

    def test_translate_to_en_returns_value_unchanged(self, access_level):
        assert access_level.translate("Open", EN) == "Open"

    def test_translate_unknown_value_returns_original(self, access_level):
        assert access_level.translate("Unknown", FR) == "Unknown"

    def test_translate_unknown_lang_returns_original(self, access_level):
        de = LanguageAlpha2("de")
        assert access_level.translate("Open", de) == "Open"


# ── available_languages ───────────────────────────────────────────────────

class TestAvailableLanguages:
    def test_returns_all_langs(self, access_level):
        assert access_level.available_languages() == (EN, FR, ES)

    def test_two_lang(self, two_lang):
        assert two_lang.available_languages() == (EN, FR)


# ── _validate ─────────────────────────────────────────────────────────────

class TestValidate:
    def test_accept_english_value(self, access_level):
        assert access_level._validate("Open") == "Open"

    def test_accept_translated_value_returns_en(self, access_level):
        assert access_level._validate("Ouvert") == "Open"
        assert access_level._validate("Abierto") == "Open"

    def test_non_string_raises(self, access_level):
        with pytest.raises(ValueError, match="Expected string"):
            access_level._validate(42)

    def test_invalid_value_raises(self, access_level):
        with pytest.raises(ValueError, match="Invalid value 'Nope'"):
            access_level._validate("Nope")


# ── Pydantic integration ─────────────────────────────────────────────────

class TestPydanticValidation:
    def test_model_accepts_en_value(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        m = M(level="Open")
        assert m.level == "Open"

    def test_model_normalises_translated_value(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        m = M(level="Ouvert")
        assert m.level == "Open"

    def test_model_rejects_invalid(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        with pytest.raises(ValidationError):
            M(level="BadValue")

    def test_serialization_with_lang_context(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        m = M(level="Open")
        dumped = m.model_dump(context={"lang": FR})
        assert dumped["level"] == "Ouvert"

    def test_serialization_with_es_context(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        m = M(level="Restricted")
        dumped = m.model_dump(context={"lang": ES})
        assert dumped["level"] == "Restringido"

    def test_serialization_no_context_defaults_en(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        m = M(level="Open")
        dumped = m.model_dump(context={"lang": EN})
        assert dumped["level"] == "Open"

    def test_json_serialization(self, access_level):
        class M(BaseModel):
            level: access_level  # type: ignore

        m = M(level="Open")
        raw = m.model_dump_json(context={"lang": FR})
        assert json.loads(raw)["level"] == "Ouvert"


# ── Edge cases ────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_single_term(self):
        tl = TranslatedLiteral(EN, FR)(("Solo", "Seul"),)
        assert tl.en_values == {"Solo"}
        assert tl.translate("Solo", FR) == "Seul"

    def test_same_word_across_languages(self):
        tl = TranslatedLiteral(EN, FR)(("Piano", "Piano"),)
        assert tl._validate("Piano") == "Piano"
        assert tl.translate("Piano", FR) == "Piano"

    def test_multiple_terms_share_no_collision(self, access_level):
        # All translated values map back correctly
        for en_val in access_level.en_values:
            assert access_level.to_en[en_val] == en_val
