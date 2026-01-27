__all__ = ["i18n_value"]

from .types import PossiblyI18nText


def i18n_value(v: PossiblyI18nText, lang: str, default: str = "") -> str:
    """
    TODO
    :param v: Possibly-internationalized text (either dictionary of ISO 3166-1 alpha-2 --> text, or just plain text.)
    :param lang: Language (ISO 3166-1 alpha-2)
    :param default: Default value if a language key is not present in an internationalized text dictionary.
    :return: The text value, internationalized if possible.
    """
    if isinstance(v, str):
        return v
    v_vals = tuple(v.values())
    return v.get(lang, v_vals[0] if v_vals else default)
