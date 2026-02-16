import pytest

from bento_lib.i18n import (
    EN,
    ES,
    FR,
    TranslatedLiteral,
)


@pytest.fixture
def access_level():
    return TranslatedLiteral(EN, FR, ES)(
        ("Open", "Ouvert", "Abierto"),
        ("Restricted", "Restreint", "Restringido"),
        ("Embargoed", "Sous embargo", "Embargado"),
    )


@pytest.fixture
def two_lang():
    return TranslatedLiteral(EN, FR)(
        ("Yes", "Oui"),
        ("No", "Non"),
    )