from dataclasses import dataclass

from villaz_router.config import EligibilityConfig, ScoringConfig
from villaz_router.eligibility import _is_scoring_result_eligible
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.matcher import match_evidence_set
from villaz_router.normalization import normalize_text
from villaz_router.models import (
    Domain,
    Intent,
    Profile,
    Route,
    RouteCandidate,
    RouteDecision,
    RouteRequest,
    RouteState,
    RoutingMode,
    RoutingReason,
    RulesetSnapshot,
    ScoringResult,
)
from villaz_router.scoring import score_evidence_matches


@dataclass(frozen=True, slots=True)
class _TargetEvaluation:
    target_id: str
    scoring: ScoringResult
    eligible: bool


def _evaluate_targets(
    normalized_message: str,
    targets: tuple[Domain | Intent, ...],
    scoring_config: ScoringConfig,
    eligibility_config: EligibilityConfig,
) -> dict[str, _TargetEvaluation]:
    evaluations: dict[str, _TargetEvaluation] = {}

    for target in sorted(targets, key=lambda item: item.id):
        matches = match_evidence_set(
            normalized_message,
            target.evidence,
        )
        scoring = score_evidence_matches(
            matches,
            target.evidence,
            scoring_config,
        )
        evaluations[target.id] = _TargetEvaluation(
            target_id=target.id,
            scoring=scoring,
            eligible=_is_scoring_result_eligible(
                scoring,
                eligibility_config,
            ),
        )

    return evaluations



@dataclass(frozen=True, slots=True)
class _QualifiedRoute:
    route_id: str
    profile: str
    priority: int
    comparison_score: int
    intent_id: str | None
    intent_route_capable: bool


def _build_qualified_routes(
    routes: tuple[Route, ...],
    profiles: tuple[Profile, ...],
    intents: tuple[Intent, ...],
    domain_evaluations: dict[str, _TargetEvaluation],
    intent_evaluations: dict[str, _TargetEvaluation],
) -> tuple[_QualifiedRoute, ...]:
    profiles_by_id = {profile.id: profile for profile in profiles}
    intents_by_id = {intent.id: intent for intent in intents}
    qualified_routes: list[_QualifiedRoute] = []

    for route in sorted(routes, key=lambda item: item.id):
        if not route.enabled:
            continue

        domain_evaluation = None
        intent_evaluation = None

        if route.when.domain is not None:
            domain_evaluation = domain_evaluations.get(route.when.domain)
            if domain_evaluation is None:
                raise RouterError(
                    RouterErrorCode.INVALID_RULESET,
                    f"route {route.id} references missing domain evaluation {route.when.domain}",
                )

        if route.when.intent is not None:
            intent_evaluation = intent_evaluations.get(route.when.intent)
            if intent_evaluation is None:
                raise RouterError(
                    RouterErrorCode.INVALID_RULESET,
                    f"route {route.id} references missing intent evaluation {route.when.intent}",
                )

        domain_satisfied = (
            domain_evaluation is None or domain_evaluation.eligible
        )
        intent_satisfied = (
            intent_evaluation is None or intent_evaluation.eligible
        )
        if not (domain_satisfied and intent_satisfied):
            continue

        profile = profiles_by_id.get(route.result.profile)
        if profile is None or not profile.enabled:
            raise RouterError(
                RouterErrorCode.INVALID_RULESET,
                f"qualified route {route.id} targets missing or disabled profile {route.result.profile}",
            )

        intent_id = route.when.intent
        intent_route_capable = False
        if intent_id is not None:
            intent = intents_by_id.get(intent_id)
            if intent is None or not intent.route_capable:
                raise RouterError(
                    RouterErrorCode.INVALID_RULESET,
                    f"qualified route {route.id} requires route-capable intent {intent_id}",
                )
            intent_route_capable = True

        if intent_evaluation is not None:
            comparison_score = intent_evaluation.scoring.score
        elif domain_evaluation is not None:
            comparison_score = domain_evaluation.scoring.score
        else:
            raise RouterError(
                RouterErrorCode.INVALID_RULESET,
                f"qualified route {route.id} has no evaluable condition",
            )

        qualified_routes.append(
            _QualifiedRoute(
                route_id=route.id,
                profile=profile.id,
                priority=route.priority,
                comparison_score=comparison_score,
                intent_id=intent_id,
                intent_route_capable=intent_route_capable,
            )
        )

    return tuple(qualified_routes)



def _get_route_capable_intent_conflict_candidates(
    qualified_routes: tuple[_QualifiedRoute, ...],
) -> tuple[_QualifiedRoute, ...] | None:
    intent_ids = {
        route.intent_id
        for route in qualified_routes
        if route.intent_route_capable and route.intent_id is not None
    }

    if len(intent_ids) < 2:
        return None

    candidates = tuple(
        route
        for route in qualified_routes
        if route.intent_id in intent_ids
        and route.intent_route_capable
    )

    route_ids = tuple(route.route_id for route in candidates)
    if len(route_ids) != len(set(route_ids)):
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            "duplicate qualified route_id detected",
        )

    return tuple(
        sorted(
            candidates,
            key=lambda route: (-route.comparison_score, route.route_id),
        )
    )

def _retain_highest_priority_routes(
    qualified_routes: tuple[_QualifiedRoute, ...],
) -> tuple[_QualifiedRoute, ...]:
    if not qualified_routes:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            "cannot reduce priority over an empty qualified route set",
        )

    max_priority = max(route.priority for route in qualified_routes)
    return tuple(
        route
        for route in qualified_routes
        if route.priority == max_priority
    )


def _resolve_routes_by_margin(
    top_priority_routes: tuple[_QualifiedRoute, ...],
    minimum_margin: int,
) -> tuple[_QualifiedRoute | None, tuple[_QualifiedRoute, ...]]:
    if len(top_priority_routes) < 2:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            "margin resolution requires at least two top-priority routes",
        )
    if minimum_margin < 0:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            "minimum_margin cannot be negative",
        )

    ordered = tuple(
        sorted(
            top_priority_routes,
            key=lambda route: (-route.comparison_score, route.route_id),
        )
    )
    top_score = ordered[0].comparison_score
    top_tied = tuple(
        route for route in ordered if route.comparison_score == top_score
    )

    if len(top_tied) >= 2:
        if minimum_margin == 0:
            return None, top_tied
        candidates = tuple(
            route
            for route in ordered
            if top_score - route.comparison_score < minimum_margin
        )
        return None, candidates

    leader = ordered[0]
    second_score = ordered[1].comparison_score
    gap = top_score - second_score

    if gap >= minimum_margin:
        return leader, ()

    candidates = tuple(
        route
        for route in ordered
        if top_score - route.comparison_score < minimum_margin
    )
    if len(candidates) < 2:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            "ambiguous margin result requires at least two candidates",
        )
    return None, candidates
_ROUTING_REASON_BY_PROFILE: dict[str, RoutingReason] = {
    "code-review-security": RoutingReason.SECURITY_REVIEW_DETECTED,
    "fiscal-finance": RoutingReason.FISCAL_FINANCE_DETECTED,
    "docs-dev": RoutingReason.DOCUMENTATION_INTENT_DETECTED,
    "unity-dev": RoutingReason.UNITY_DETECTED,
    "mobile-dev": RoutingReason.MOBILE_DETECTED,
}


def _routing_reason_for_profile(profile_id: str) -> RoutingReason:
    try:
        return _ROUTING_REASON_BY_PROFILE[profile_id]
    except KeyError as exc:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            f"no runtime routing reason mapped for profile {profile_id}",
        ) from exc


def _to_route_candidates(
    routes: tuple[_QualifiedRoute, ...],
) -> tuple[RouteCandidate, ...]:
    route_ids = tuple(route.route_id for route in routes)
    if len(route_ids) != len(set(route_ids)):
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            "duplicate qualified route_id detected",
        )

    return tuple(
        RouteCandidate(
            route_id=route.route_id,
            profile=route.profile,
            comparison_score=route.comparison_score,
        )
        for route in sorted(
            routes,
            key=lambda item: (-item.comparison_score, item.route_id),
        )
    )


def _runtime_profiles_by_id(
    ruleset: RulesetSnapshot,
) -> dict[str, Profile]:
    return {profile.id: profile for profile in ruleset.profiles}


def decide_route(
    request: RouteRequest,
    ruleset: RulesetSnapshot,
) -> RouteDecision:
    profiles_by_id = _runtime_profiles_by_id(ruleset)

    if request.explicit_profile is not None:
        profile = profiles_by_id.get(request.explicit_profile)
        if profile is None or not profile.enabled:
            raise RouterError(
                RouterErrorCode.INVALID_PROFILE,
                f"invalid or disabled explicit profile {request.explicit_profile}",
            )

        return RouteDecision(
            state=RouteState.EXPLICIT,
            profile=profile.id,
            route_id=None,
            comparison_score=None,
            mode=RoutingMode.MANUAL,
            reason=RoutingReason.USER_SELECTED_PROFILE,
            conflict_resolved=False,
            candidates=(),
        )

    normalized_message = normalize_text(request.message)

    domain_evaluations = _evaluate_targets(
        normalized_message,
        ruleset.domains,
        ruleset.router.scoring,
        ruleset.router.eligibility,
    )
    intent_evaluations = _evaluate_targets(
        normalized_message,
        ruleset.intents,
        ruleset.router.scoring,
        ruleset.router.eligibility,
    )

    qualified_routes = _build_qualified_routes(
        ruleset.routes,
        ruleset.profiles,
        ruleset.intents,
        domain_evaluations,
        intent_evaluations,
    )

    if not qualified_routes:
        return RouteDecision(
            state=RouteState.UNROUTED,
            profile=None,
            route_id=None,
            comparison_score=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.INSUFFICIENT_EVIDENCE,
            conflict_resolved=False,
            candidates=(),
        )

    conflict_candidates = _get_route_capable_intent_conflict_candidates(
        qualified_routes
    )
    if conflict_candidates is not None:
        return RouteDecision(
            state=RouteState.AMBIGUOUS,
            profile=None,
            route_id=None,
            comparison_score=None,
            mode=RoutingMode.AUTO,
            reason=RoutingReason.AMBIGUOUS_ROUTE,
            conflict_resolved=False,
            candidates=_to_route_candidates(conflict_candidates),
        )

    top_priority_routes = _retain_highest_priority_routes(qualified_routes)

    if len(top_priority_routes) == 1:
        winner = top_priority_routes[0]
        return RouteDecision(
            state=RouteState.ROUTED,
            profile=winner.profile,
            route_id=winner.route_id,
            comparison_score=winner.comparison_score,
            mode=RoutingMode.AUTO,
            reason=_routing_reason_for_profile(winner.profile),
            conflict_resolved=len(qualified_routes) > 1,
            candidates=(),
        )

    winner, ambiguous_routes = _resolve_routes_by_margin(
        top_priority_routes,
        ruleset.router.ambiguity.minimum_margin,
    )

    if winner is not None:
        return RouteDecision(
            state=RouteState.ROUTED,
            profile=winner.profile,
            route_id=winner.route_id,
            comparison_score=winner.comparison_score,
            mode=RoutingMode.AUTO,
            reason=_routing_reason_for_profile(winner.profile),
            conflict_resolved=True,
            candidates=(),
        )

    return RouteDecision(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        conflict_resolved=False,
        candidates=_to_route_candidates(ambiguous_routes),
    )
