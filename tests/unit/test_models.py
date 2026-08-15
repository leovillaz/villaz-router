import pytest
from pydantic import ValidationError

from villaz_router.models import (
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
        mode=RoutingMode.AUTO,
        reason=RoutingReason.MOBILE_DETECTED,
    )

    assert decision.profile == "mobile-dev"


def test_ambiguous_requires_null_profile() -> None:
    decision = RouteDecision(
        state=RouteState.AMBIGUOUS,
        profile=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        candidates=("docs-dev", "mobile-dev"),
    )

    assert decision.profile is None
    assert decision.candidates == ("docs-dev", "mobile-dev")


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
