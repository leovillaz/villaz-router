from villaz_router.normalization import normalize_text


def test_normalize_text_applies_approved_pipeline() -> None:
    assert normalize_text("  Tributação   de NF-e  ") == "tributacao de nf-e"
    assert normalize_text("FIREBASE") == "firebase"
    assert normalize_text("Code   Review") == "code review"


def test_normalize_text_is_accent_insensitive() -> None:
    assert normalize_text("Café") == "cafe"
    assert normalize_text("TÉCNICO") == "tecnico"


def test_normalize_text_casefolds_unicode() -> None:
    assert normalize_text("Straße") == "strasse"


def test_normalize_text_applies_nfkc_compatibility() -> None:
    assert normalize_text("ＦＩＲＥＢＡＳＥ") == "firebase"


def test_normalize_text_collapses_unicode_whitespace() -> None:
    assert normalize_text("  code\n\t\treview ") == "code review"


def test_normalize_text_preserves_punctuation() -> None:
    assert normalize_text("Erro na NF-E: C# / C++.") == "erro na nf-e: c# / c++."


def test_normalize_text_allows_empty_message() -> None:
    assert normalize_text("") == ""
    assert normalize_text("      ") == ""
    assert normalize_text("\n\t\r") == ""
