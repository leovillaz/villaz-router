from dataclasses import dataclass

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.http_api.models import (
    AmbiguousCandidate,
    ErrorEnvelope,
    ErrorResponse,
    PromptRequest,
)
from villaz_router.models import RouteDecision, RouteRequest, RouteState
from villaz_router.router import decide_route


@dataclass(frozen=True, slots=True)
class HttpRoutingError:
    status_code: int
    body: ErrorResponse


type PromptRoutingOutcome = RouteDecision | HttpRoutingError


def route_prompt_request(
    prompt_request: PromptRequest,
    runtime_context: RuntimeContext,
) -> PromptRoutingOutcome:
    route_request = RouteRequest(
        message=prompt_request.message,
        explicit_profile=prompt_request.explicit_profile,
    )

    try:
        decision = decide_route(route_request, runtime_context.ruleset)
    except RouterError as exc:
        if exc.code is not RouterErrorCode.INVALID_PROFILE:
            raise
        return HttpRoutingError(
            status_code=422,
            body=ErrorResponse(
                error=ErrorEnvelope(
                    code="INVALID_PROFILE",
                    message="The explicit profile is invalid or disabled.",
                )
            ),
        )

    if decision.state in {RouteState.EXPLICIT, RouteState.ROUTED}:
        return decision

    if decision.state is RouteState.AMBIGUOUS:
        candidates = tuple(
            AmbiguousCandidate(
                route_id=candidate.route_id,
                profile=candidate.profile,
                comparison_score=candidate.comparison_score,
            )
            for candidate in decision.candidates
        )
        return HttpRoutingError(
            status_code=409,
            body=ErrorResponse(
                error=ErrorEnvelope(
                    code="AMBIGUOUS_ROUTE",
                    message="The request matches multiple routes.",
                    candidates=candidates,
                )
            ),
        )

    if decision.state is RouteState.UNROUTED:
        return HttpRoutingError(
            status_code=422,
            body=ErrorResponse(
                error=ErrorEnvelope(
                    code="UNROUTED",
                    message="The request could not be routed.",
                )
            ),
        )

    raise RuntimeError(f"Unsupported route decision state: {decision.state!r}")
