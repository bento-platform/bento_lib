from .types import PossiblyI18nText

__all__ = ["i18n_value"]


def i18n_value(v: PossiblyI18nText, lang: str) -> str:
    """
    Given either a plain string or an internationalized text dictionary, return either a string in the correct language,
    the untranslated string if a translated text dictionary is not passed, or the first available value if the language
    is not present in the dictionary:
        {"en": "hello", "fr": "bonjour"} with a requested language "en" would return "hello".
        {"en": "hello", "fr": "bonjour"} with a requested language "fr" would return "bonjour".
        {"en": "hello", "fr": "bonjour"} with a requested language "es" would return "hello".
    :param v: Possibly-internationalized text (either dictionary of ISO 3166-1 alpha-2 --> text, or just plain text.)
    :param lang: Language (ISO 3166-1 alpha-2)
    :return: The text value, internationalized if possible.
    """
    if isinstance(v, str):
        return v
    v_vals = tuple(v.values())
    return v.get(lang, v_vals[0] if v_vals else "")
