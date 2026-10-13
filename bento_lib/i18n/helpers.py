from pydantic_extra_types.language_code import LanguageAlpha2

from .typing import EN, FR, TRANSLATED_STRING_ADAPTER, TranslatedString, TranslatedStringFallbackPolicy

__all__ = ["render_translated_text"]

DEFAULT_FALLBACK: tuple[LanguageAlpha2, ...] = (EN, FR)


def render_translated_text(
    instance: TranslatedString,
    lang: LanguageAlpha2,
    fallback: tuple[LanguageAlpha2, ...] = DEFAULT_FALLBACK,
    policy: TranslatedStringFallbackPolicy = "first",
):
    return TRANSLATED_STRING_ADAPTER.dump_python(
        instance, mode="json", context={"lang": lang, "lang_fallback": fallback, "lang_fallback_policy": policy}
    )
