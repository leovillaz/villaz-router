from pathlib import Path

import pytest

from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.loader import load_ruleset_snapshot
from villaz_router.models import RouteRequest, RouteState, RoutingMode, RoutingReason
from villaz_router.router import decide_route


@pytest.fixture(scope="module")
def snapshot():
    return load_ruleset_snapshot(Path.cwd())


def _equalize_mobile_unity_priority(snapshot):
    routes = tuple(
        route.model_copy(update={"priority": 300})
        if route.id == "ROUTE-MOBILE-001"
        else route
        for route in snapshot.routes
    )
    return snapshot.model_copy(update={"routes": routes})


def test_decide_route_explicit_profile_has_absolute_precedence(snapshot) -> None:
    broken_routes = tuple(
        route.model_copy(
            update={
                "when": route.when.model_copy(update={"domain": "missing-domain"})
            }
        )
        if route.id == "ROUTE-MOBILE-001"
        else route
        for route in snapshot.routes
    )
    broken_snapshot = snapshot.model_copy(update={"routes": broken_routes})

    decision = decide_route(
        RouteRequest(
            message="flutter cfop documente code review",
            explicit_profile="mobile-dev",
        ),
        broken_snapshot,
    )

    assert decision.state is RouteState.EXPLICIT
    assert decision.profile == "mobile-dev"
    assert decision.route_id is None
    assert decision.comparison_score is None
    assert decision.mode is RoutingMode.MANUAL
    assert decision.reason is RoutingReason.USER_SELECTED_PROFILE
    assert decision.conflict_resolved is False
    assert decision.candidates == ()


def test_decide_route_invalid_explicit_profile_fails_without_fallback(snapshot) -> None:
    with pytest.raises(RouterError) as exc_info:
        decide_route(
            RouteRequest(message="flutter", explicit_profile="missing-profile"),
            snapshot,
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_PROFILE


def test_decide_route_without_qualified_route_is_unrouted(snapshot) -> None:
    decision = decide_route(RouteRequest(message="hello world"), snapshot)

    assert decision.state is RouteState.UNROUTED
    assert decision.profile is None
    assert decision.route_id is None
    assert decision.comparison_score is None
    assert decision.mode is RoutingMode.AUTO
    assert decision.reason is RoutingReason.INSUFFICIENT_EVIDENCE
    assert decision.conflict_resolved is False
    assert decision.candidates == ()


def test_decide_route_single_mobile_route_is_routed(snapshot) -> None:
    decision = decide_route(RouteRequest(message="flutter"), snapshot)

    assert decision.state is RouteState.ROUTED
    assert decision.profile == "mobile-dev"
    assert decision.route_id == "ROUTE-MOBILE-001"
    assert decision.comparison_score == 10
    assert decision.reason is RoutingReason.MOBILE_DETECTED
    assert decision.conflict_resolved is False
    assert decision.candidates == ()


def test_decide_route_priority_resolves_multiple_qualified_routes(snapshot) -> None:
    decision = decide_route(RouteRequest(message="flutter cfop"), snapshot)

    assert decision.state is RouteState.ROUTED
    assert decision.profile == "fiscal-finance"
    assert decision.route_id == "ROUTE-FISCAL-001"
    assert decision.comparison_score == 10
    assert decision.reason is RoutingReason.FISCAL_FINANCE_DETECTED
    assert decision.conflict_resolved is True


def test_decide_route_route_capable_intent_conflict_precedes_priority(snapshot) -> None:
    decision = decide_route(
        RouteRequest(message="documente code review"),
        snapshot,
    )

    assert decision.state is RouteState.AMBIGUOUS
    assert decision.profile is None
    assert decision.route_id is None
    assert decision.comparison_score is None
    assert decision.reason is RoutingReason.AMBIGUOUS_ROUTE
    assert decision.conflict_resolved is False
    assert tuple(candidate.route_id for candidate in decision.candidates) == (
        "ROUTE-DOC-001",
        "ROUTE-REVIEW-001",
    )


def test_decide_route_margin_selects_unique_leader(snapshot) -> None:
    equal_priority_snapshot = _equalize_mobile_unity_priority(snapshot)

    decision = decide_route(
        RouteRequest(message="flutter firebase unity"),
        equal_priority_snapshot,
    )

    assert decision.state is RouteState.ROUTED
    assert decision.profile == "mobile-dev"
    assert decision.route_id == "ROUTE-MOBILE-001"
    assert decision.comparison_score == 20
    assert decision.conflict_resolved is True


def test_decide_route_margin_below_threshold_is_ambiguous(snapshot) -> None:
    equal_priority_snapshot = _equalize_mobile_unity_priority(snapshot)

    decision = decide_route(
        RouteRequest(message="flutter android unity"),
        equal_priority_snapshot,
    )

    assert decision.state is RouteState.AMBIGUOUS
    assert tuple(
        (candidate.route_id, candidate.comparison_score)
        for candidate in decision.candidates
    ) == (
        ("ROUTE-MOBILE-001", 14),
        ("ROUTE-UNITY-001", 10),
    )


def test_decide_route_is_publicly_exported() -> None:
    from villaz_router import decide_route as public_decide_route

    assert public_decide_route is decide_route


def test_decide_route_disabled_explicit_profile_fails_without_fallback(snapshot) -> None:
    profiles = tuple(
        profile.model_copy(update={"enabled": False})
        if profile.id == "mobile-dev"
        else profile
        for profile in snapshot.profiles
    )
    disabled_snapshot = snapshot.model_copy(update={"profiles": profiles})

    with pytest.raises(RouterError) as exc_info:
        decide_route(
            RouteRequest(message="flutter", explicit_profile="mobile-dev"),
            disabled_snapshot,
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_PROFILE


def test_decide_route_missing_runtime_reason_mapping_is_invalid_ruleset(snapshot) -> None:
    source_profile = next(
        profile for profile in snapshot.profiles if profile.id == "mobile-dev"
    )
    custom_profile = source_profile.model_copy(update={"id": "custom-dev"})
    profiles = snapshot.profiles + (custom_profile,)

    routes = tuple(
        route.model_copy(
            update={
                "result": route.result.model_copy(update={"profile": "custom-dev"})
            }
        )
        if route.id == "ROUTE-MOBILE-001"
        else route
        for route in snapshot.routes
    )
    custom_snapshot = snapshot.model_copy(
        update={"profiles": profiles, "routes": routes}
    )

    with pytest.raises(RouterError) as exc_info:
        decide_route(RouteRequest(message="flutter"), custom_snapshot)

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET
