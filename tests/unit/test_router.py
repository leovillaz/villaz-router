from dataclasses import FrozenInstanceError

import pytest

from villaz_router.config import EligibilityConfig, ScoringConfig
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.models import (
    Domain,
    EvidenceContribution,
    Evidence,
    EvidenceStrength,
    EvidenceType,
    Intent,
    Profile,
    Route,
    RouteCondition,
    RouteResult,
    ScoringResult,
)
from villaz_router.router import (
    _QualifiedRoute,
    _TargetEvaluation,
    _build_qualified_routes,
    _evaluate_targets,
    _get_route_capable_intent_conflict_candidates,
    _retain_highest_priority_routes,
    _resolve_routes_by_margin,
)


SCORING_CONFIG = ScoringConfig(strong=10, medium=4, weak=1)
ELIGIBILITY_CONFIG = EligibilityConfig(
    minimum_score=10,
    weak_only_cannot_qualify=True,
)


def _evidence(
    evidence_id: str,
    value: str,
    strength: EvidenceStrength = EvidenceStrength.STRONG,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        type=EvidenceType.TERM,
        strength=strength,
        value=value,
    )


def test_target_evaluation_is_frozen() -> None:
    evaluation = _TargetEvaluation(
        target_id="mobile",
        scoring=ScoringResult(score=0, contributions=()),
        eligible=False,
    )

    with pytest.raises(FrozenInstanceError):
        evaluation.eligible = True


def test_evaluate_domains_keeps_all_targets_in_canonical_id_order() -> None:
    targets = (
        Domain(
            id="z-mobile",
            evidence=(_evidence("MOBILE-001", "flutter"),),
        ),
        Domain(
            id="a-fiscal",
            evidence=(_evidence("FISCAL-001", "icms"),),
        ),
    )

    evaluations = _evaluate_targets(
        "flutter",
        targets,
        SCORING_CONFIG,
        ELIGIBILITY_CONFIG,
    )

    assert tuple(evaluations) == ("a-fiscal", "z-mobile")
    assert evaluations["a-fiscal"].target_id == "a-fiscal"
    assert evaluations["a-fiscal"].scoring.score == 0
    assert evaluations["a-fiscal"].scoring.contributions == ()
    assert evaluations["a-fiscal"].eligible is False
    assert evaluations["z-mobile"].scoring.score == 10
    assert evaluations["z-mobile"].eligible is True


def test_evaluate_intents_uses_same_intermediate_contract() -> None:
    targets = (
        Intent(
            id="review-security",
            route_capable=True,
            evidence=(_evidence("REVIEW-001", "review"),),
        ),
        Intent(
            id="question",
            route_capable=False,
            evidence=(_evidence("QUESTION-001", "question"),),
        ),
    )

    evaluations = _evaluate_targets(
        "review",
        targets,
        SCORING_CONFIG,
        ELIGIBILITY_CONFIG,
    )

    assert evaluations["review-security"].scoring.score == 10
    assert evaluations["review-security"].eligible is True
    assert evaluations["question"].scoring.score == 0
    assert evaluations["question"].eligible is False


def test_route_capable_does_not_change_intent_scoring_or_eligibility() -> None:
    targets = (
        Intent(
            id="a-route-capable",
            route_capable=True,
            evidence=(_evidence("A-001", "docs"),),
        ),
        Intent(
            id="b-auxiliary",
            route_capable=False,
            evidence=(_evidence("B-001", "docs"),),
        ),
    )

    evaluations = _evaluate_targets(
        "docs",
        targets,
        SCORING_CONFIG,
        ELIGIBILITY_CONFIG,
    )

    assert evaluations["a-route-capable"].scoring.score == 10
    assert evaluations["b-auxiliary"].scoring.score == 10
    assert evaluations["a-route-capable"].eligible is True
    assert evaluations["b-auxiliary"].eligible is True


def _evaluation(
    target_id: str,
    score: int,
    eligible: bool,
) -> _TargetEvaluation:
    if score == 0:
        scoring = ScoringResult(score=0, contributions=())
    else:
        scoring = ScoringResult(
            score=score,
            contributions=(
                EvidenceContribution(
                    evidence_id=f"{target_id}-E",
                    strength=EvidenceStrength.STRONG,
                    weight=score,
                ),
            ),
        )
    return _TargetEvaluation(
        target_id=target_id,
        scoring=scoring,
        eligible=eligible,
    )


def _route(
    route_id: str,
    *,
    domain: str | None = None,
    intent: str | None = None,
    profile: str = "profile-a",
    priority: int = 100,
    enabled: bool = True,
) -> Route:
    return Route(
        id=route_id,
        enabled=enabled,
        priority=priority,
        when=RouteCondition(domain=domain, intent=intent),
        result=RouteResult(profile=profile),
    )


def test_qualified_route_is_frozen() -> None:
    qualified = _QualifiedRoute(
        route_id="route-a",
        profile="profile-a",
        priority=100,
        comparison_score=10,
        intent_id=None,
        intent_route_capable=False,
    )

    with pytest.raises(FrozenInstanceError):
        qualified.priority = 200


def test_build_qualified_routes_domain_only_uses_exact_domain_score() -> None:
    qualified = _build_qualified_routes(
        routes=(_route("route-domain", domain="mobile"),),
        profiles=(Profile(id="profile-a", enabled=True),),
        intents=(),
        domain_evaluations={
            "mobile": _evaluation("mobile", 14, True),
            "unity": _evaluation("unity", 20, True),
        },
        intent_evaluations={},
    )

    assert qualified == (
        _QualifiedRoute(
            route_id="route-domain",
            profile="profile-a",
            priority=100,
            comparison_score=14,
            intent_id=None,
            intent_route_capable=False,
        ),
    )


def test_build_qualified_routes_intent_only_uses_exact_intent_score() -> None:
    qualified = _build_qualified_routes(
        routes=(_route("route-review", intent="review-security"),),
        profiles=(Profile(id="profile-a", enabled=True),),
        intents=(
            Intent(
                id="review-security",
                route_capable=True,
                evidence=(),
            ),
        ),
        domain_evaluations={},
        intent_evaluations={
            "review-security": _evaluation("review-security", 18, True),
            "documentation": _evaluation("documentation", 30, True),
        },
    )

    assert qualified[0].comparison_score == 18
    assert qualified[0].intent_id == "review-security"
    assert qualified[0].intent_route_capable is True


def test_build_qualified_routes_domain_and_intent_requires_both_and_uses_intent_score() -> None:
    qualified = _build_qualified_routes(
        routes=(
            _route(
                "route-combined",
                domain="security",
                intent="review-security",
            ),
        ),
        profiles=(Profile(id="profile-a", enabled=True),),
        intents=(
            Intent(
                id="review-security",
                route_capable=True,
                evidence=(),
            ),
        ),
        domain_evaluations={
            "security": _evaluation("security", 20, True),
        },
        intent_evaluations={
            "review-security": _evaluation("review-security", 12, True),
        },
    )

    assert len(qualified) == 1
    assert qualified[0].comparison_score == 12


def test_unsatisfied_route_is_omitted_before_profile_validation() -> None:
    qualified = _build_qualified_routes(
        routes=(
            _route(
                "route-unsatisfied",
                domain="mobile",
                profile="missing-profile",
            ),
        ),
        profiles=(),
        intents=(),
        domain_evaluations={
            "mobile": _evaluation("mobile", 4, False),
        },
        intent_evaluations={},
    )

    assert qualified == ()


def test_route_resolves_all_declared_references_before_boolean_and() -> None:
    with pytest.raises(RouterError) as exc_info:
        _build_qualified_routes(
            routes=(
                _route(
                    "route-invalid",
                    domain="security",
                    intent="missing-intent",
                ),
            ),
            profiles=(Profile(id="profile-a", enabled=True),),
            intents=(),
            domain_evaluations={
                "security": _evaluation("security", 4, False),
            },
            intent_evaluations={},
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET


@pytest.mark.parametrize(
    "profiles",
    (
        (),
        (Profile(id="profile-a", enabled=False),),
    ),
)
def test_qualified_route_requires_existing_enabled_profile(
    profiles: tuple[Profile, ...],
) -> None:
    with pytest.raises(RouterError) as exc_info:
        _build_qualified_routes(
            routes=(_route("route-domain", domain="mobile"),),
            profiles=profiles,
            intents=(),
            domain_evaluations={
                "mobile": _evaluation("mobile", 10, True),
            },
            intent_evaluations={},
        )

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET


def test_disabled_route_is_skipped_before_condition_resolution() -> None:
    qualified = _build_qualified_routes(
        routes=(
            _route(
                "route-disabled",
                domain="missing-domain",
                profile="missing-profile",
                enabled=False,
            ),
        ),
        profiles=(),
        intents=(),
        domain_evaluations={},
        intent_evaluations={},
    )

    assert qualified == ()


def test_qualified_routes_are_materialized_in_route_id_order() -> None:
    qualified = _build_qualified_routes(
        routes=(
            _route("z-route", domain="mobile", priority=200),
            _route("a-route", domain="mobile", priority=100),
        ),
        profiles=(Profile(id="profile-a", enabled=True),),
        intents=(),
        domain_evaluations={
            "mobile": _evaluation("mobile", 10, True),
        },
        intent_evaluations={},
    )

    assert tuple(route.route_id for route in qualified) == (
        "a-route",
        "z-route",
    )


def _qualified_route(
    route_id: str,
    *,
    priority: int = 100,
    comparison_score: int = 10,
    intent_id: str | None = None,
) -> _QualifiedRoute:
    return _QualifiedRoute(
        route_id=route_id,
        profile=f"profile-{route_id}",
        priority=priority,
        comparison_score=comparison_score,
        intent_id=intent_id,
        intent_route_capable=intent_id is not None,
    )


def test_no_route_capable_intent_conflict_returns_none() -> None:
    routes = (
        _qualified_route("route-a", intent_id="review-security"),
        _qualified_route("route-b", intent_id="review-security"),
    )

    assert _get_route_capable_intent_conflict_candidates(routes) is None


def test_two_distinct_route_capable_intents_create_conflict() -> None:
    routes = (
        _qualified_route(
            "route-docs",
            priority=400,
            comparison_score=18,
            intent_id="documentation",
        ),
        _qualified_route(
            "route-review",
            priority=500,
            comparison_score=14,
            intent_id="review-security",
        ),
    )

    candidates = _get_route_capable_intent_conflict_candidates(routes)

    assert candidates is not None
    assert tuple(route.route_id for route in candidates) == (
        "route-docs",
        "route-review",
     )


def test_domain_only_route_is_excluded_from_intent_conflict_candidates() -> None:
    routes = (
        _qualified_route(
            "route-docs",
            comparison_score=18,
            intent_id="documentation",
        ),
        _qualified_route(
            "route-review",
            comparison_score=14,
            intent_id="review-security",
        ),
        _qualified_route(
            "route-fiscal",
            priority=450,
            comparison_score=20,
            intent_id=None,
        ),
    )

    candidates = _get_route_capable_intent_conflict_candidates(routes)

    assert candidates is not None
    assert tuple(route.route_id for route in candidates) == (
        "route-docs",
        "route-review",
     )


def test_multiple_routes_for_same_conflicting_intent_are_all_preserved() -> None:
    routes = (
        _qualified_route("route-docs-a", comparison_score=20, intent_id="documentation"),
        _qualified_route("route-docs-b", comparison_score=18, intent_id="documentation"),
        _qualified_route("route-review", comparison_score=14, intent_id="review-security"),
    )

    candidates = _get_route_capable_intent_conflict_candidates(routes)

    assert candidates is not None
    assert tuple(route.route_id for route in candidates) == (
        "route-docs-a",
        "route-docs-b",
        "route-review",
    )


def test_conflict_candidates_are_canonically_ordered_by_score_then_route_id() -> None:
    routes = (
        _qualified_route("route-z", comparison_score=10, intent_id="review-security"),
        _qualified_route("route-b", comparison_score=20, intent_id="documentation"),
        _qualified_route("route-a", comparison_score=20, intent_id="documentation"),
    )

    candidates = _get_route_capable_intent_conflict_candidates(routes)

    assert candidates is not None
    assert tuple(route.route_id for route in candidates) == (
        "route-a",
        "route-b",
        "route-z",
     )

def test_retain_highest_priority_routes_eliminates_lower_priority_even_with_higher_score() -> None:
    routes = (
        _qualified_route(
            "route-high-score-low-priority",
            priority=450,
            comparison_score=20,
        ),
        _qualified_route(
            "route-low-score-high-priority",
            priority=500,
            comparison_score=10,
        ),
    )

    retained = _retain_highest_priority_routes(routes)

    assert tuple(route.route_id for route in retained) == (
        "route-low-score-high-priority",
    )


def test_retain_highest_priority_routes_preserves_all_equal_max_priority_routes() -> None:
    routes = (
        _qualified_route("route-a", priority=500, comparison_score=10),
        _qualified_route("route-b", priority=500, comparison_score=20),
        _qualified_route("route-c", priority=450, comparison_score=30),
    )

    retained = _retain_highest_priority_routes(routes)

    assert tuple(route.route_id for route in retained) == (
        "route-a",
        "route-b",
    )


def test_retain_highest_priority_routes_does_not_use_score_as_tiebreak() -> None:
    routes = (
        _qualified_route("route-a", priority=500, comparison_score=10),
        _qualified_route("route-b", priority=500, comparison_score=99),
    )

    retained = _retain_highest_priority_routes(routes)

    assert retained == routes


def test_retain_highest_priority_routes_rejects_empty_input() -> None:
    with pytest.raises(RouterError) as exc_info:
        _retain_highest_priority_routes(())

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET

def test_margin_exactly_equal_to_minimum_selects_unique_leader() -> None:
    routes = (
        _qualified_route("route-a", comparison_score=20),
        _qualified_route("route-b", comparison_score=15),
    )

    winner, candidates = _resolve_routes_by_margin(routes, 5)

    assert winner is not None
    assert winner.route_id == "route-a"
    assert candidates == ()


def test_margin_below_minimum_is_ambiguous() -> None:
    routes = (
        _qualified_route("route-a", comparison_score=20),
        _qualified_route("route-b", comparison_score=17),
    )

    winner, candidates = _resolve_routes_by_margin(routes, 5)

    assert winner is None
    assert tuple(route.route_id for route in candidates) == ("route-a", "route-b")



def test_top_score_tie_is_always_ambiguous_with_positive_margin() -> None:
    routes = (
        _qualified_route("route-b", comparison_score=20),
        _qualified_route("route-a", comparison_score=20),
        _qualified_route("route-c", comparison_score=10),
    )

    winner, candidates = _resolve_routes_by_margin(routes, 5)

    assert winner is None
    assert tuple(route.route_id for route in candidates) == (
        "route-a",
        "route-b",
    )


def test_top_score_tie_is_always_ambiguous_with_vero_margin() -> None:
    routes = (
        _qualified_route("route-b", comparison_score=20),
        _qualified_route("route-a", comparison_score=20),
        _qualified_route("route-c", comparison_score=15),
    )

    winner, candidates = _resolve_routes_by_margin(routes, 0)

    assert winner is None
    assert tuple(route.route_id for route in candidates) == (
        "route-a",
        "route-b",
    )


def test_ambiguous_margin_candidates_use_strict_band() -> None:
    routes = (
        _qualified_route("route-a", comparison_score=20),
        _qualified_route("route-b", comparison_score=17),
        _qualified_route("route-c", comparison_score=16),
        _qualified_route("route-d", comparison_score=15),
        _qualified_route("route-e", comparison_score=10),
    )

    winner, candidates = _resolve_routes_by_margin(routes, 5)

    assert winner is None
    assert tuple(route.route_id for route in candidates) == (
        "route-a",
        "route-b",
        "route-c",
    )


def test_ambiguous_margin_candidates_are_canonically_ordered() -> None:
    routes = (
        _qualified_route("route-b", comparison_score=20),
        _qualified_route("route-a", comparison_score=20),
        _qualified_route("route-c", comparison_score=18),
    )

    winner, candidates = _resolve_routes_by_margin(routes, 5)

    assert winner is None
    assert tuple(route.route_id for route in candidates) == (
        "route-a",
        "route-b",
        "route-c",
    )

