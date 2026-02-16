from __future__ import annotations
from pydantic import BaseModel, GetCoreSchemaHandler, SerializationInfo
from pydantic_core import core_schema
from typing import Any, override
from pydantic_extra_types.language_code import LanguageAlpha2


EN = LanguageAlpha2("en")
ES = LanguageAlpha2("es")
FR = LanguageAlpha2("fr")

class TranslatedLiteral:
    """
    Usage:
        AccessLevel = TranslatedLiteral(EN, FR, ES)(
            ("Open", "Ouvert", "Abierto"),
            ("Restricted", "Restreint", "Restringido"),
            ("Embargoed", "Sous embargo", "Embargado"),
        )
    """

    def __init__(self, *langs: LanguageAlpha2):
        if not langs or langs[0] != EN:
            raise ValueError("First language must be 'en' (canonical)")
        self.langs = langs

    def __call__(self, *terms: tuple[str, ...]) -> TranslatedLiteral:
        """Bind term tuples to the language sequence. Returns self for chaining."""
        for t in terms:
            if len(t) != len(self.langs):
                raise ValueError(
                    f"Term {t} has {len(t)} values, expected {len(self.langs)} "
                    f"for languages {self.langs}"
                )

        self.en_values = {t[0] for t in terms}

        # {"Open": {"fr": "Ouvert", "es": "Abierto"}, ...}
        self.translations: dict[str, dict[str, str]] = {}
        for t in terms:
            en_key = t[0]
            self.translations[en_key] = {
                lang: t[i] for i, lang in enumerate(self.langs) if i > 0
            }

        # Reverse lookup: any translated value -> English key
        self.to_en: dict[str, str] = {}
        for t in terms:
            for val in t:
                self.to_en[val] = t[0]

        return self

    def translate(self, value: str, lang: LanguageAlpha2) -> str:
        if lang == EN:
            return value
        return self.translations.get(value, {}).get(lang, value)

    def available_languages(self) -> tuple[LanguageAlpha2, ...]:
        return self.langs

    def _validate(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value).__name__}")
        if value in self.en_values:
            return value
        if value in self.to_en:
            return self.to_en[value]
        raise ValueError(
            f"Invalid value '{value}'. "
            f"Accepted values: {sorted(self.to_en.keys())}"
        )
    
    def _serialize(self, v: str, info: SerializationInfo) -> Any:
        lang = info.context.get("lang") if info.context else EN
        return self.translate(v, lang) 

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            self._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                self._serialize,
                info_arg=True,
            ),
        )


# --- Translatable base model ---
class TranslatableModel(BaseModel):
    language: LanguageAlpha2 = EN
    
    def _inject_lang_context(self, kwargs: dict) -> dict:
        ctx = kwargs.get("context") or {}
        ctx["lang"] = self.language
        kwargs["context"] = ctx
        return kwargs

    @override
    def model_dump(self, **kwargs) -> dict:
        return super().model_dump(**self._inject_lang_context(kwargs))

    @override
    def model_dump_json(self, **kwargs) -> str:
        return super().model_dump_json(**self._inject_lang_context(kwargs))


