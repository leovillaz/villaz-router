from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """Return the deterministic text representation used for matching."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.casefold()

    decomposed = unicodedata.normalize("NFD", normalized)
    without_diacritics = "".join(
        char
        for char in decomposed
        if not unicodedata.combining(char)
     )

    recomposed = unicodedata.normalize(
        "NFKC",
        without_diacritics,
    )

    return " ".join(recomposed.split())
