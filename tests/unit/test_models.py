import pytest
from pydantic import ValidationError

from villaz_router.models import (
    EvidenceContribution,
    EvidenceMatch,
    EvidenceStrength,
    EvidenceType,
    ScoringResult,
    RouteCandidate,
    RouteDecision,
    RouteRequest,
    RouteState,
    RoutingMode,
    RoutingReason,
)


def test_route_request_accepts_only_expected_fields() -> None:
    request = RouteRequest(
        message="Teste",
        explicit_profile=None,
    )

    assert request.message == "Teste"
    assert request.explicit_profile is None


def test_route_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RouteRequest(
            message="Teste",
            explicit_profile=None,
            unknown_field="invalid",
        )


def test_explicit_decision_requires_profile_and_manual_mode() -> None:
    decision = RouteDecision(
        state=RouteState.EXPLICIT,
        profile="unity-dev",
        mode=RoutingMode.MANUAL,
        reason=RoutingReason.USER_SELECTED_PROFILE,
    )

    assert decision.profile == "unity-dev"


def test_explicit_without_profile_is_invalid() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.EXPLICIT,
            profile=None,
            mode=RoutingMode.MANUAL,
            reason=RoutingReason.USER_SELECTED_PROFILE,
        )


def test_explicit_with_auto_mode_is_invalid() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.EXPLICIT,
            profile="unity-dev",
            mode=RoutingMode.AUTO,
            reason=RoutingReason.USER_SELECTED_PROFILE,
        )


def test_routed_requires_profile_and_auto_mode() -> None:
    decision = RouteDecision(
        state=RouteState.ROUTED,
        profile="mobile-dev",
        route_id="route-mobile",
        comparison_score=18,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.MOBILE_DETECTED,
    )

    assert decision.profile == "mobile-dev"
    assert decision.route_id == "route-mobile"
    assert decision.comparison_score == 18


def test_ambiguous_requires_null_profile() -> None:
    candidates = (
        RouteCandidate(
            route_id="route-docs",
            profile="docs-dev",
            comparison_score=20,
        ),
        RouteCandidate(
            route_id="route-mobile",
            profile="mobile-dev",
            comparison_score=17,
        ),
    )

    decision = RouteDecision(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        candidates=candidates,
    )

    assert decision.profile is None
    assert decision.candidates == candidates


def test_unrouted_requires_null_profile() -> None:
    decision = RouteDecision(
        state=RouteState.UNROUTED,
        profile=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.INSUFFICIENT_EVIDENCE,
    )

    assert decision.profile is None


def test_candidates_cannot_have_duplicates() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.AMBIGUOUS,
            profile=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.AMBIGUOUS_ROUTE,
            candidates=("docs-dev", "docs-dev"),
        )


def test_explicit_requires_user_selected_reason() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.EXPLICIT,
            profile="unity-dev",
            mode=RoutingMode.MANUAL,
            reason=RoutingReason.UNITY_DETECTED,
        )


def test_routed_rejects_uncertain_reason() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.ROUTED,
            profile="mobile-dev",
            mode=RoutingMode.AUTO,
            reason=RoutingReason.AMBIGUOUS_ROUTE,
        )


def test_successful_decision_rejects_candidates() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.ROUTED,
            profile="mobile-dev",
            mode=RoutingMode.AUTO,
            reason=RoutingReason.MOBILE_DETECTED,
            candidates=("unity-dev",),
        )


def test_non_routed_decision_rejects_resolved_conflict() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.AMBIGUOUS,
            profile=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.AMBIGUOUS_ROUTE,
            conflict_resolved=True,
            candidates=("docs-dev", "mobile-dev"),
        )



def test_evidence_match_accepts_valid_contract() -> None:
    match = EvidenceMatch(
        evidence_id="DOMAIN-MOBILE-001",
        evidence_type=EvidenceType.TERM,
        evidence_value="flutter",
        start=10,
        end=17,
    )

    assert match.evidence_id == "DOMAIN-MOBILE-001"
    assert match.evidence_type is EvidenceType.TERM
    assert match.evidence_value == "flutter"
    assert match.start == 10
    assert match.end == 17


def test_evidence_match_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        EvidenceMatch(
            evidence_id="E-001",
            evidence_type="term",
            evidence_value="flutter",
            start=0,
            end=7,
            unknown_field="invalid",
        )


def test_evidence_match_is_immutable() -> None:
    match = EvidenceMatch(
        evidence_id="E-001",
        evidence_type="term",
        evidence_value="flutter",
        start=0,
        end=7,
    )

    with pytest.raises(ValidationError):
        match.start = 1


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("evidence_id", ""),
        ("evidence_value", ""),
    ),
)
def test_evidence_match_rejects_empty_identity_fields(
    field: str,
    value: str,
) -> None:
    payload = {
        "evidence_id": "E-001",
        "evidence_type": "term",
        "evidence_value": "flutter",
        "start": 0,
        "end": 7,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        EvidenceMatch(**payload)


def test_evidence_match_rejects_negative_start() -> None:
    with pytest.raises(ValidationError):
        EvidenceMatch(
            evidence_id="E-001",
            evidence_type="term",
            evidence_value="flutter",
            start=-1,
            end=7,
        )


@pytest.mark.parametrize("end", (0, 4))
def test_evidence_match_requires_end_greater_than_start(end: int) -> None:
    with pytest.raises(ValidationError):
        EvidenceMatch(
            evidence_id="E-001",
            evidence_type="term",
            evidence_value="flutter",
            start=4,
            end=end,
        )


def test_evidence_match_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        EvidenceMatch(
            evidence_id="E-001",
            evidence_type="regex",
            evidence_value="flutter",
            start=0,
            end=7,
        )


def test_evidence_contribution_accepts_valid_contract() -> None:
    contribution = EvidenceContribution(
        evidence_id="E-001",
        strength=EvidenceStrength.STRONG,
        weight=10,
    )

    assert contribution.evidence_id == "E-001"
    assert contribution.strength is EvidenceStrength.STRONG
    assert contribution.weight == 10


def test_evidence_contribution_rejects_empty_evidence_id() -> None:
    with pytest.raises(ValidationError):
        EvidenceContribution(
            evidence_id="",
            strength=EvidenceStrength.STRONG,
            weight=10,
        )


def test_evidence_contribution_rejects_non_positive_weight() -> None:
    with pytest.raises(ValidationError):
        EvidenceContribution(
            evidence_id="E-001",
            strength=EvidenceStrength.WEAK,
            weight=0,
        )


def test_evidence_contribution_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        EvidenceContribution(
            evidence_id="E-001",
            strength=EvidenceStrength.MEDIUM,
            weight=4,
            unknown_field="invalid",
        )


def test_evidence_contribution_is_immutable() -> None:
    contribution = EvidenceContribution(
        evidence_id="E-001",
        strength=EvidenceStrength.MEDIUM,
        weight=4,
    )

    with pytest.raises(ValidationError):
        contribution.weight = 10


def test_scoring_result_accepts_valid_contract() -> None:
    contributions = (
        EvidenceContribution(
            evidence_id="E-001",
            strength=EvidenceStrength.STRONG,
            weight=10,
        ),
        EvidenceContribution(
            evidence_id="E-002",
            strength=EvidenceStrength.WEAK,
            weight=1,
        ),
    )

    result = ScoringResult(
        score=11,
        contributions=contributions,
    )

    assert result.score == 11
    assert result.contributions == contributions


def test_scoring_result_accepts_empty_result() -> None:
    result = ScoringResult(score=0, contributions=())
    assert result.score == 0
    assert result.contributions == ()


def test_scoring_result_rejects_negative_score() -> None:
    with pytest.raises(ValidationError):
        ScoringResult(score=-1, contributions=())


def test_scoring_result_rejects_inconsistent_total() -> None:
    contribution = EvidenceContribution(
        evidence_id="E-001",
        strength=EvidenceStrength.STRONG,
        weight=10,
    )
    with pytest.raises(ValidationError):
        ScoringResult(score=11, contributions=(contribution,))


def test_scoring_result_rejects_nonzero_score_without_contributions() -> None:
    with pytest.raises(ValidationError):
        ScoringResult(score=1, contributions=())


def test_scoring_result_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        ScoringResult(score=0, contributions=(), unknown_field="invalid")


def test_scoring_result_is_immutable() -> None:
    result = ScoringResult(score=0, contributions=())
    with pytest.raises(ValidationError):
        result.score = 1

def test_route_candidate_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RouteCandidate(
            route_id="route-docs",
            profile="docs-dev",
            comparison_score=10,
            unknown_field="invalid",
        )


def test_route_candidate_is_immutable() -> None:
    candidate = RouteCandidate(
        route_id="route-docs",
        profile="docs-dev",
        comparison_score=10,
    )

    with pytest.raises(ValidationError):
        candidate.comparison_score = 20


def test_routed_decision_requires_route_id() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.ROUTED,
            profile="mobile-dev",
            route_id=None,
            comparison_score=10,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.MOBILE_DETECTED,
        )


def test_routed_decision_requires_comparison_score() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.ROUTED,
            profile="mobile-dev",
            route_id="route-mobile",
            comparison_score=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.MOBILE_DETECTED,
        )


def test_ambiguous_decision_requires_distinct_route_ids() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.AMBIGUOUS,
            profile=None,
            route_id=None,
            comparison_score=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.AMBIGUOUS_ROUTE,
            candidates=(
                RouteCandidate(
                    route_id="route-docs",
                    profile="docs-dev",
                    comparison_score=20,
                ),
                RouteCandidate(
                    route_id="route-docs",
                    profile="mobile-dev",
                    comparison_score=17,
                ),
            ),
        )


def test_ambiguous_decision_rejects_noncanonical_candidate_order() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.AMBIGUOUS,
            profile=None,
            route_id=None,
            comparison_score=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.AMBIGUOUS_ROUTE,
            candidates=(
                RouteCandidate(
                    route_id="route-mobile",
                    profile="mobile-dev",
                    comparison_score=17,
                ),
                RouteCandidate(
                    route_id="route-docs",
                    profile="docs-dev",
                    comparison_score=20,
                ),
            ),
        )


def test_ambiguous_decision_uses_route_id_ascending_for_equal_scores() -> None:
    candidates = (
        RouteCandidate(
            route_id="route-a",
            profile="docs-dev",
            comparison_score=20,
        ),
        RouteCandidate(
            route_id="route-b",
            profile="mobile-dev",
            comparison_score=20,
        ),
    )

    decision = RouteDecision(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        candidates=candidates,
    )

    assert decision.candidates == candidates


def test_unrouted_decision_rejects_candidates() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            state=RouteState.UNROUTED,
            profile=None,
            route_id=None,
            comparison_score=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.INSUFFICIENT_EVIDENCE,
            candidates=(
                RouteCandidate(
                    route_id="route-mobile",
                    profile="mobile-dev",
                    comparison_score=10,
                ),
                RouteCandidate(
                    route_id="route-docs",
                    profile="docs-dev",
                    comparison_score=10,
                ),
            ),
        )
