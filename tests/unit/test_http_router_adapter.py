import ast
from pathlib import Path

import pytest

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.http_api import router_adapter
from villaz_router.http_api.models import PromptRequest
from villaz_router.http_api.router_adapter import (
    HttpRoutingError,
    route_prompt_request,
)
from villaz_router.models import (
    RouteCandidate,
    RouteDecision,
    RouteRequest,
    RouteState,
    RoutingMode,
    RoutingReason,
)


def _runtime_context() -> RuntimeContext:
    return RuntimeContext.model_construct(ruleset=object())


def _dispatchable_decision(state: RouteState) -> RouteDecision:
    return RouteDecision.model_construct(
        state=state,
        profile="profile-a",
        route_id="route-a" if state is RouteState.ROUTED else None,
        comparison_score=7 if state is RouteState.ROUTED else None,
        mode=(
            RoutingMode.AUTO
            if state is RouteState.ROUTED
            else RoutingMode.MANUAL
        ),
        reason=(
            RoutingReason.MOBILE_DETECTED
            if state is RouteState.ROUTED
            else RoutingReason.USER_SELECTED_PROFILE
        ),
        conflict_resolved=False,
        candidates=(),
    )


def _capture_request(
    monkeypatch: pytest.MonkeyPatch,
    decision: RouteDecision,
) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_decide_route(
        route_request: RouteRequest,
        ruleset: object,
    ) -> RouteDecision:
        captured["route_request"] = route_request
        captured["ruleset"] = ruleset
        return decision

    monkeypatch.setattr(router_adapter, "decide_route", fake_decide_route)
    return captured


def _payload(error: HttpRoutingError) -> dict[str, object]:
    return error.body.model_dump(mode="json", exclude_none=True)


def _imported_modules() -> set[str]:
    source = Path(router_adapter.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_message_is_copied_exactly(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = _dispatchable_decision(RouteState.ROUTED)
    captured = _capture_request(monkeypatch, decision)
    prompt_request = PromptRequest(
        message="  Preserve CASE, spacing, and ç exactly.  ",
    )

    route_prompt_request(prompt_request, _runtime_context())

    route_request = captured["route_request"]
    assert isinstance(route_request, RouteRequest)
    assert route_request.message == prompt_request.message


def test_explicit_profile_is_copied_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _dispatchable_decision(RouteState.EXPLICIT)
    captured = _capture_request(monkeypatch, decision)
    prompt_request = PromptRequest(
        message="message",
        explicit_profile="  Profile-A  ",
    )

    route_prompt_request(prompt_request, _runtime_context())

    route_request = captured["route_request"]
    assert isinstance(route_request, RouteRequest)
    assert route_request.explicit_profile == prompt_request.explicit_profile


def test_runtime_ruleset_is_passed_by_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _dispatchable_decision(RouteState.ROUTED)
    captured = _capture_request(monkeypatch, decision)
    runtime_context = _runtime_context()

    route_prompt_request(PromptRequest(message="message"), runtime_context)

    assert captured["ruleset"] is runtime_context.ruleset


def test_explicit_returns_original_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _dispatchable_decision(RouteState.EXPLICIT)
    _capture_request(monkeypatch, decision)

    outcome = route_prompt_request(
        PromptRequest(message="message", explicit_profile="profile-a"),
        _runtime_context(),
    )

    assert outcome is decision


def test_routed_returns_original_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _dispatchable_decision(RouteState.ROUTED)
    _capture_request(monkeypatch, decision)

    outcome = route_prompt_request(
        PromptRequest(message="message"),
        _runtime_context(),
    )

    assert outcome is decision


def test_ambiguous_returns_exact_public_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = RouteDecision.model_construct(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        conflict_resolved=False,
        candidates=(
            RouteCandidate(
                route_id="route-b",
                profile="profile-b",
                comparison_score=11,
            ),
            RouteCandidate(
                route_id="route-a",
                profile="profile-a",
                comparison_score=11,
            ),
        ),
    )
    _capture_request(monkeypatch, decision)

    outcome = route_prompt_request(
        PromptRequest(message="message"),
        _runtime_context(),
    )

    assert isinstance(outcome, HttpRoutingError)
    assert outcome.status_code == 409
    assert _payload(outcome) == {
        "error": {
            "code": "AMBIGUOUS_ROUTE",
            "message": "The request matches multiple routes.",
            "candidates": [
                {
                    "route_id": "route-b",
                    "profile": "profile-b",
                    "comparison_score": 11,
                },
                {
                    "route_id": "route-a",
                    "profile": "profile-a",
                    "comparison_score": 11,
                },
            ],
        }
    }


def test_ambiguous_candidates_preserve_decision_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidates = (
        RouteCandidate(
            route_id="route-z",
            profile="profile-z",
            comparison_score=5,
        ),
        RouteCandidate(
            route_id="route-a",
            profile="profile-a",
            comparison_score=5,
        ),
        RouteCandidate(
            route_id="route-m",
            profile="profile-m",
            comparison_score=5,
        ),
    )
    decision = RouteDecision.model_construct(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        conflict_resolved=False,
        candidates=candidates,
    )
    _capture_request(monkeypatch, decision)

    outcome = route_prompt_request(
        PromptRequest(message="message"),
        _runtime_context(),
    )

    assert isinstance(outcome, HttpRoutingError)
    payload_candidates = _payload(outcome)["error"]["candidates"]
    assert [candidate["route_id"] for candidate in payload_candidates] == [
        candidate.route_id for candidate in candidates
    ]


def test_unrouted_returns_exact_error_without_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = RouteDecision.model_construct(
        state=RouteState.UNROUTED,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.INSUFFICIENT_EVIDENCE,
        conflict_resolved=False,
        candidates=(),
    )
    _capture_request(monkeypatch, decision)

    outcome = route_prompt_request(
        PromptRequest(message="message"),
        _runtime_context(),
    )

    assert isinstance(outcome, HttpRoutingError)
    assert outcome.status_code == 422
    assert _payload(outcome) == {
        "error": {
            "code": "UNROUTED",
            "message": "The request could not be routed.",
        }
    }


def _raise_router_error(
    monkeypatch: pytest.MonkeyPatch,
    error: RouterError,
) -> None:
    def fake_decide_route(
        route_request: RouteRequest,
        ruleset: object,
    ) -> RouteDecision:
        raise error

    monkeypatch.setattr(router_adapter, "decide_route", fake_decide_route)


def test_invalid_profile_returns_exact_public_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = RouterError(
        RouterErrorCode.INVALID_PROFILE,
        "sensitive internal profile diagnostic",
    )
    _raise_router_error(monkeypatch, error)

    outcome = route_prompt_request(
        PromptRequest(message="message", explicit_profile="invalid"),
        _runtime_context(),
    )

    assert isinstance(outcome, HttpRoutingError)
    assert outcome.status_code == 422
    assert _payload(outcome) == {
        "error": {
            "code": "INVALID_PROFILE",
            "message": "The explicit profile is invalid or disabled.",
        }
    }


def test_invalid_profile_never_exposes_router_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    internal_message = "private router details must not escape"
    _raise_router_error(
        monkeypatch,
        RouterError(RouterErrorCode.INVALID_PROFILE, internal_message),
    )

    outcome = route_prompt_request(
        PromptRequest(message="message", explicit_profile="invalid"),
        _runtime_context(),
    )

    assert isinstance(outcome, HttpRoutingError)
    assert internal_message not in repr(_payload(outcome))


@pytest.mark.parametrize(
    "error_code",
    [
        RouterErrorCode.INVALID_RULESET,
        RouterErrorCode.INVALID_SCORING_INPUT,
    ],
)
def test_other_router_errors_propagate_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    error_code: RouterErrorCode,
) -> None:
    error = RouterError(error_code, "internal diagnostic")
    _raise_router_error(monkeypatch, error)

    with pytest.raises(RouterError) as exc_info:
        route_prompt_request(
            PromptRequest(message="message"),
            _runtime_context(),
        )

    assert exc_info.value is error


def test_adapter_does_not_depend_on_dispatcher() -> None:
    assert not {
        module
        for module in _imported_modules()
        if module.startswith("villaz_router.dispatcher")
    }


def test_adapter_does_not_depend_on_ollama() -> None:
    assert not {
        module
        for module in _imported_modules()
        if module == "ollama"
        or module.startswith("ollama.")
        or module.startswith("villaz_router.ollama_execution")
    }
