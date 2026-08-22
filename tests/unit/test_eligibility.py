from villaz_router.config import EligibilityConfig
from villaz_router.eligibility import _is_scoring_result_eligible
from villaz_router.models import (
    EvidenceContribution,
    EvidenceStrength,
    ScoringResult,
)


def _contribution(
    evidence_id: str,
    strength: EvidenceStrength,
    weight: int,
) -> EvidenceContribution:
    return EvidenceContribution(
        evidence_id=evidence_id,
        strength=strength,
        weight=weight,
    )


def _result(
    *contributions: EvidenceContribution,
) -> ScoringResult:
    return ScoringResult(
        score=sum(item.weight for item in contributions),
        contributions=contributions,
    )


def _config(
    minimum_score: int = 10,
    weak_only_cannot_qualify: bool = True,
) -> EligibilityConfig:
    return EligibilityConfig(
        minimum_score=minimum_score,
        weak_only_cannot_qualify=weak_only_cannot_qualify,
    )


def test_score_below_threshold_is_ineligible() -> None:
    result = _result(
        _contribution("E-001", EvidenceStrength.MEDIUM, 4),
        _contribution("E-002", EvidenceStrength.MEDIUM, 4),
    )

    assert _is_scoring_result_eligible(result, _config()) is False


def test_score_equal_to_threshold_is_eligible_with_strong() -> None:
    result = _result(
        _contribution("E-001", EvidenceStrength.STRONG, 10),
    )

    assert _is_scoring_result_eligible(result, _config()) is True


def test_score_above_threshold_is_eligible_with_medium() -> None:
    result = _result(
        _contribution("E-001", EvidenceStrength.MEDIUM, 4),
        _contribution("E-002", EvidenceStrength.MEDIUM, 4),
        _contribution("E-003", EvidenceStrength.MEDIUM, 4),
    )

    assert _is_scoring_result_eligible(result, _config()) is True


def test_weak_only_is_ineligible_when_gate_enabled() -> None:
    contributions = tuple(
        _contribution(
            f"E-{index:03d}",
            EvidenceStrength.WEAK,
            1,
        )
        for index in range(1, 11)
    )
    result = _result(*contributions)

    assert _is_scoring_result_eligible(result, _config()) is False


def test_weak_only_can_qualify_when_gate_disabled() -> None:
    contributions = tuple(
        _contribution(
            f"E-{index:03d}",
            EvidenceStrength.WEAK,
            1,
        )
        for index in range(1, 11)
    )
    result = _result(*contributions)

    assert (
        _is_scoring_result_eligible(
            result,
            _config(weak_only_cannot_qualify=False),
        )
        is True
    )


def test_medium_breaks_weak_only_gate() -> None:
    result = _result(
        _contribution("E-001", EvidenceStrength.MEDIUM, 4),
        *(
            _contribution(
                f"E-{index:03d}",
                EvidenceStrength.WEAK,
                1,
            )
            for index in range(2, 8)
        ),
    )

    assert _is_scoring_result_eligible(result, _config()) is True


def test_empty_result_is_ineligible() -> None:
    result = ScoringResult(score=0, contributions=())

    assert _is_scoring_result_eligible(result, _config()) is False


def test_eligibility_is_invariant_to_contribution_order() -> None:
    contributions = (
        _contribution("E-001", EvidenceStrength.MEDIUM, 4),
        _contribution("E-002", EvidenceStrength.WEAK, 1),
        _contribution("E-003", EvidenceStrength.WEAK, 1),
        _contribution("E-004", EvidenceStrength.WEAK, 1),
        _contribution("E-005", EvidenceStrength.WEAK, 1),
        _contribution("E-006", EvidenceStrength.WEAK, 1),
        _contribution("E-007", EvidenceStrength.WEAK, 1),
    )
    forward = _result(*contributions)
    reverse = _result(*reversed(contributions))

    assert _is_scoring_result_eligible(forward, _config()) is True
    assert _is_scoring_result_eligible(reverse, _config()) is True
