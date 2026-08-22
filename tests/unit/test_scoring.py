import pytest

from villaz_router.config import ScoringConfig
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.models import (
    Evidence,
    EvidenceMatch,
    EvidenceStrength,
    EvidenceType,
)
from villaz_router.scoring import score_evidence_matches


def _evidence(
    evidence_id: str,
    strength: EvidenceStrength,
    value: str,
    evidence_type: EvidenceType = EvidenceType.TERM,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        type=evidence_type,
        strength=strength,
        value=value,
    )


def _match(
    evidence_id: str,
    value: str,
    evidence_type: EvidenceType = EvidenceType.TERM,
) -> EvidenceMatch:
    return EvidenceMatch(
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        evidence_value=value,
        start=0,
        end=len(value),
    )


def _scoring() -> ScoringConfig:
    return ScoringConfig(
        strong=10,
        medium=4,
        weak=1,
    )


def test_score_evidence_matches_returns_empty_result() -> None:
    result = score_evidence_matches(
        (),
        (),
        _scoring(),
    )

    assert result.score == 0
    assert result.contributions == ()


def test_score_evidence_matches_uses_configured_weights() -> None:
    evidence_items = (
        _evidence("E-STRONG", EvidenceStrength.STRONG, "strong"),
        _evidence("E-MEDIUM", EvidenceStrength.MEDIUM, "medium"),
        _evidence("E-WEAK", EvidenceStrength.WEAK, "weak"),
    )
    matches = (
        _match("E-STRONG", "strong"),
        _match("E-MEDIUM", "medium"),
        _match("E-WEAK", "weak"),
    )
    scoring = ScoringConfig(
        strong=17,
        medium=5,
        weak=2,
    )

    result = score_evidence_matches(
        matches,
        evidence_items,
        scoring,
    )

    assert result.score == 24
    assert tuple(
        contribution.weight
        for contribution in result.contributions
    ) == (5, 17, 2)


def test_score_is_invariant_to_input_order() -> None:
    evidence_items = (
        _evidence("E-B", EvidenceStrength.WEAK, "beta"),
        _evidence("E-A", EvidenceStrength.STRONG, "alpha"),
    )
    matches = (
        _match("E-B", "beta"),
        _match("E-A", "alpha"),
    )

    result = score_evidence_matches(
        reversed(matches),
        reversed(evidence_items),
        _scoring(),
    )

    assert result.score == 11
    assert tuple(
        contribution.evidence_id
        for contribution in result.contributions
    ) == ("E-A", "E-B")


def test_score_accepts_generators() -> None:
    evidence_items = (
        _evidence("E-001", EvidenceStrength.MEDIUM, "flutter"),
    )
    matches = (
        _match("E-001", "flutter"),
    )

    result = score_evidence_matches(
        (match for match in matches),
        (evidence for evidence in evidence_items),
        _scoring(),
    )

    assert result.score == 4


def test_duplicate_evidence_id_fails_before_duplicate_match() -> None:
    evidence_items = (
        _evidence("E-B", EvidenceStrength.STRONG, "one"),
        _evidence("E-B", EvidenceStrength.WEAK, "two"),
    )
    matches = (
        _match("E-A", "alpha"),
        _match("E-A", "alpha"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(
            matches,
            evidence_items,
            _scoring(),
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_SCORING_INPUT
    assert exc_info.value.message == "duplicate evidence id: E-B"


def test_duplicate_evidence_uses_lexicographically_smallest_id() -> None:
    evidence_items = (
        _evidence("E-Z", EvidenceStrength.STRONG, "zeta"),
        _evidence("E-Z", EvidenceStrength.STRONG, "zeta"),
        _evidence("E-A", EvidenceStrength.WEAK, "alpha"),
        _evidence("E-A", EvidenceStrength.WEAK, "alpha"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(
            (),
            evidence_items,
            _scoring(),
        )

    assert exc_info.value.message == "duplicate evidence id: E-A"


def test_duplicate_match_uses_lexicographically_smallest_id() -> None:
    evidence_items = (
        _evidence("E-A", EvidenceStrength.STRONG, "alpha"),
        _evidence("E-Z", EvidenceStrength.WEAK, "zeta"),
    )
    matches = (
        _match("E-Z", "zeta"),
        _match("E-Z", "zeta"),
        _match("E-A", "alpha"),
        _match("E-A", "alpha"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(
            matches,
            evidence_items,
            _scoring(),
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_SCORING_INPUT
    assert exc_info.value.message == "duplicate evidence match id: E-A"


def test_unknown_evidence_uses_lexicographically_smallest_id() -> None:
    matches = (
        _match("E-Z", "zeta"),
        _match("E-A", "alpha"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(
            matches,
            (),
            _scoring(),
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_SCORING_INPUT
    assert exc_info.value.message == (
        "evidence match references unknown evidence_id: E-A"
    )


def test_type_mismatch_precedes_value_mismatch() -> None:
    evidence_items = (
        _evidence(
            "E-TYPE",
            EvidenceStrength.STRONG,
            "flutter",
            EvidenceType.TERM,
        ),
        _evidence(
            "E-VALUE",
            EvidenceStrength.WEAK,
            "original",
            EvidenceType.TERM,
        ),
    )
    matches = (
        _match(
            "E-TYPE",
            "flutter",
            EvidenceType.PHRASE,
        ),
        _match(
            "E-VALUE",
            "different",
            EvidenceType.TERM,
        ),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(
            matches,
            evidence_items,
            _scoring(),
        )

    assert exc_info.value.message == (
        "evidence match type does not match configured evidence: E-TYPE"
    )


def test_value_mismatch_is_exact() -> None:
    evidence_items = (
        _evidence(
            "E-001",
            EvidenceStrength.STRONG,
            "Flutter",
        ),
    )
    matches = (
        _match(
            "E-001",
            "flutter",
        ),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(
            matches,
            evidence_items,
            _scoring(),
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_SCORING_INPUT
    assert exc_info.value.message == (
        "evidence match value does not match configured evidence: E-001"
    )


def test_unmatched_configured_evidence_does_not_contribute() -> None:
    evidence_items = (
        _evidence("E-001", EvidenceStrength.STRONG, "alpha"),
        _evidence("E-002", EvidenceStrength.STRONG, "beta"),
    )
    matches = (
        _match("E-001", "alpha"),
    )

    result = score_evidence_matches(
        matches,
        evidence_items,
        _scoring(),
    )

    assert result.score == 10
    assert len(result.contributions) == 1
    assert result.contributions[0].evidence_id == "E-001"


def test_duplicate_match_precedes_unknown_reference() -> None:
    evidence_items = (
        _evidence("E-DUP", EvidenceStrength.STRONG, "dup"),
    )
    matches = (
        _match("E-DUP", "dup"),
        _match("E-DUP", "dup"),
        _match("E-UNKNOWN", "unknown"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(matches, evidence_items, _scoring())

    assert exc_info.value.code is RouterErrorCode.INVALID_SCORING_INPUT
    assert exc_info.value.message == "duplicate evidence match id: E-DUP"


def test_unknown_reference_precedes_type_mismatch() -> None:
    evidence_items = (
        _evidence("E-TYPE", EvidenceStrength.STRONG, "flutter"),
    )
    matches = (
        _match("E-TYPE", "flutter", EvidenceType.PHRASE),
        _match("E-UNKNOWN", "unknown"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(matches, evidence_items, _scoring())

    assert exc_info.value.code is RouterErrorCode.INVALID_SCORING_INPUT
    assert exc_info.value.message == (
        "evidence match references unknown evidence_id: E-UNKNOWN"
    )


def test_type_mismatch_uses_lexicographically_smallest_id() -> None:
    evidence_items = (
        _evidence("E-Z", EvidenceStrength.STRONG, "zeta", EvidenceType.TERM),
        _evidence("E-A", EvidenceStrength.WEAK, "alpha", EvidenceType.TERM),
    )
    matches = (
        _match("E-Z", "zeta", EvidenceType.PHRASE),
        _match("E-A", "alpha", EvidenceType.PHRASE),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(matches, evidence_items, _scoring())

    assert exc_info.value.message == (
        "evidence match type does not match configured evidence: E-A"
    )


def test_value_mismatch_uses_lexicographically_smallest_id() -> None:
    evidence_items = (
        _evidence("E-Z", EvidenceStrength.STRONG, "zeta"),
        _evidence("E-A", EvidenceStrength.WEAK, "alpha"),
    )
    matches = (
        _match("E-Z", "wrong-z"),
        _match("E-A", "wrong-a"),
    )

    with pytest.raises(RouterError) as exc_info:
        score_evidence_matches(matches, evidence_items, _scoring())

    assert exc_info.value.message == (
        "evidence match value does not match configured evidence: E-A"
    )
