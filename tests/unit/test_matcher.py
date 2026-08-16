from villaz_router.matcher import match_evidence, match_evidence_set
from villaz_router.models import Evidence
from villaz_router.normalization import normalize_text


def _evidence(
    evidence_id: str,
    evidence_type: str,
    value: str,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        type=evidence_type,
        strength="strong",
        value=value,
    )


def test_phrase_matches_literal_continuous_substring() -> None:
    message = normalize_text(
        "Preciso fazer CODE   REVIEW deste projeto"
    )
    match = match_evidence(
        message,
        _evidence("E-001", "phrase", "Code Review"),
    )

    assert match is not None
    assert match.evidence_value == "Code Review"
    assert message[match.start:match.end] == "code review"


def test_term_matches_complete_term() -> None:
    message = normalize_text("Estou usando Dart com Flutter")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "dart"),
    )

    assert match is not None
    assert message[match.start:match.end] == "dart"


def test_term_rejects_internal_substring() -> None:
    message = normalize_text("dartboard")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "dart"),
    )

    assert match is None


def test_term_treats_numbers_as_word_characters() -> None:
    message = normalize_text("dart2")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "dart"),
    )

    assert match is None


def test_term_treats_underscore_as_word_character() -> None:
    message = normalize_text("dart_core")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "dart"),
    )

    assert match is None


def test_term_accepts_punctuation_as_external_boundary() -> None:
    message = normalize_text("firebase, auth")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "firebase"),
    )

    assert match is not None


def test_term_preserves_internal_punctuation_literal() -> None:
    message = normalize_text("Erro na NF-E. Programacao em C#.")
    nf_e = match_evidence(
        message,
        _evidence("E-001", "term", "nf-e"),
    )
    csharp = match_evidence(
        message,
        _evidence("E-002", "term", "c#"),
    )

    assert nf_e is not None
    assert csharp is not None
    assert message[nf_e.start:nf_e.end] == "nf-e"
    assert message[csharp.start:csharp.end] == "c#"


def test_term_returns_first_valid_occurrence_not_first_invalid_one() -> None:
    message = normalize_text("dartboard dart")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "dart"),
    )

    assert match is not None
    assert match.start == len("dartboard ")


def test_match_preserves_original_evidence_value() -> None:
    message = normalize_text("erro na tributacao")
    match = match_evidence(
        message,
        _evidence("E-001", "term", "Tributação"),
    )

    assert match is not None
    assert match.evidence_value == "Tributação"


def test_empty_normalized_message_has_no_match() -> None:
    match = match_evidence(
        "",
        _evidence("E-001", "term", "flutter"),
    )

    assert match is None


def test_matching_set_returns_each_evidence_at_most_once() -> None:
    message = normalize_text("firebase firebase firebase")
    matches = match_evidence_set(
        message,
        (
            _evidence("E-001", "term", "firebase"),
        ),
    )

    assert tuple(match.evidence_id for match in matches) == ("E-001",)


def test_matching_set_allows_distinct_overlapping_evidence() -> None:
    message = normalize_text("preciso de code review")
    matches = match_evidence_set(
        message,
        (
            _evidence("E-002", "term", "review"),
            _evidence("E-001", "phrase", "code review"),
        ),
    )

    assert tuple(match.evidence_id for match in matches) == (
        "E-001",
        "E-002",
    )


def test_matching_set_orders_deterministically_by_evidence_id() -> None:
    message = normalize_text("flutter dart firebase")
    matches = match_evidence_set(
        message,
        (
            _evidence("E-003", "term", "firebase"),
            _evidence("E-001", "term", "flutter"),
            _evidence("E-002", "term", "dart"),
        ),
    )

    assert tuple(match.evidence_id for match in matches) == (
        "E-001",
        "E-002",
        "E-003",
    )


def test_matching_set_empty_message_returns_empty_tuple() -> None:
    matches = match_evidence_set(
        "",
        (
            _evidence("E-001", "term", "flutter"),
        ),
    )

    assert matches == ()
