import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.dispatcher_models import DispatchPlan
from villaz_router.http_api import create_app

from villaz_router.ollama_execution.errors import (
    OllamaExecutionError,
    OllamaExecutionErrorCode,
    OllamaExecutionStage,
)
from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)
from villaz_router.ollama_execution.models import (
    OllamaExecutionRequest,
    OllamaExecutionResult,
)

ROOT = Path(__file__).resolve().parents[2]
ROUTER_MATRIX_PATH = (
    ROOT
    / "tests"
    / "regression"
    / "router_v1_cases.json"
)

EXPECTED_REGISTRY_HASH = (
    "c9b7ef321815b11f6a38fcd0c4b3538b"
    "c549e78a41a1149760e3c49f8dcbf6af"
)


def load_normative_router_case(
    case_id: str,
) -> dict[str, object]:
    document = json.loads(
        ROUTER_MATRIX_PATH.read_text(
            encoding="utf-8"
        )
    )
    matches = [
        case
        for case in document["cases"]
        if case["id"] == case_id
    ]

    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one normative case {case_id}"
        )

    return matches[0]


def assert_runtime_context_absent(application: object) -> None:
    with pytest.raises(AttributeError):
        application.state.runtime_context

def assert_ollama_executor_absent(
    application: object,
) -> None:
    with pytest.raises(AttributeError):
        application.state.ollama_executor

def test_official_http_application_is_ready() -> None:
    application = create_app(ROOT)
    assert_runtime_context_absent(application)
    assert_ollama_executor_absent(application)

    with TestClient(application) as client:
        context = application.state.runtime_context

        executor = application.state.ollama_executor

        assert isinstance(
            executor,
            OllamaExecutor,
        )
        assert isinstance(context, RuntimeContext)
        assert context.configuration_root == ROOT
        assert len(context.ruleset.ruleset_hash) == 64
        int(context.ruleset.ruleset_hash, 16)

        registry = context.profile_registry

        assert (
            registry.registry_hash
            == EXPECTED_REGISTRY_HASH
        )
        assert len(registry.profiles) == 5
        assert all(
            profile.enabled
            for profile in registry.profiles
        )

        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")

        assert live_response.status_code == 200
        assert live_response.json() == {
            "status": "alive",
        }
        assert ready_response.status_code == 200
        assert ready_response.json() == {
            "status": "ready",
        }

    assert_runtime_context_absent(application)


def test_official_health_responses_expose_no_runtime_data() -> None:
    application = create_app(ROOT)

    with TestClient(application) as client:
        payloads = (
            client.get("/health/live").json(),
            client.get("/health/ready").json(),
        )

    assert payloads == (
        {"status": "alive"},
        {"status": "ready"},
    )

    serialized = repr(payloads)

    assert EXPECTED_REGISTRY_HASH not in serialized
    assert str(ROOT) not in serialized
    assert "system_prompt" not in serialized
    assert "model" not in serialized

def test_official_readiness_does_not_execute_ollama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fail_if_executed(
        self: OllamaExecutor,
        request: object,
    ) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError(
            "readiness must not execute ollama"
        )

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fail_if_executed,
    )

    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }
    assert calls == 0


def test_official_application_enforces_raw_body_limit() -> None:
    application = create_app(ROOT)

    with TestClient(application) as client:
        accepted_response = client.post(
            "/health/live",
            content=b"a" * 65_536,
        )
        rejected_response = client.post(
            "/health/live",
            content=b"a" * 65_537,
        )

    assert accepted_response.status_code == 405
    assert accepted_response.json() == {
        "detail": "Method Not Allowed",
    }
    assert rejected_response.status_code == 413
    assert rejected_response.json() == {
        "error": {
            "code": "REQUEST_TOO_LARGE",
            "message": (
                "The request body exceeds the maximum "
                "allowed size."
            ),
        }
    }


def test_official_prompt_executes_explicit_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[OllamaExecutionRequest] = []

    async def fake_execute(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        requests.append(request)
        return OllamaExecutionResult(
            model=request.dispatch_plan.model,
            response_text="Explicit generated response.",
        )

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fake_execute,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.post(
            "/v1/prompt",
            json={
                "message": "Meu Rigidbody não funciona.",
                "explicit_profile": "mobile-dev",
            },
        )

    assert response.status_code == 200
    assert len(requests) == 1
    plan = requests[0].dispatch_plan
    assert response.json() == {
        "response": "Explicit generated response.",
        "profile": plan.profile_id,
        "model": plan.model,
        "state": "explicit",
        "route_id": None,
    }
    assert plan.profile_id == "mobile-dev"
    assert plan.route_id is None
    assert requests[0].user_prompt == "Meu Rigidbody não funciona."


def test_official_prompt_executes_deterministic_routed_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[OllamaExecutionRequest] = []

    async def fake_execute(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        requests.append(request)
        return OllamaExecutionResult(
            model=request.dispatch_plan.model,
            response_text="Routed generated response.",
        )

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fake_execute,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.post(
            "/v1/prompt",
            json={
                "message": "Existe SQL Injection neste trecho C#?",
            },
        )

    assert response.status_code == 200
    assert len(requests) == 1
    plan = requests[0].dispatch_plan
    assert response.json() == {
        "response": "Routed generated response.",
        "profile": plan.profile_id,
        "model": plan.model,
        "state": "routed",
        "route_id": plan.route_id,
    }
    assert plan.profile_id == "code-review-security"
    assert plan.route_id is not None


def test_official_prompt_executes_normative_rt_017_unity_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = load_normative_router_case("RT-017")
    message = case["message"]
    expected_state = case["expected_state"]
    expected_profile = case["expected_profile"]

    assert isinstance(message, str)
    assert case["requested_profile"] == "auto"
    assert isinstance(expected_state, str)
    assert isinstance(expected_profile, str)
    assert case["expected_error"] is None

    requests: list[OllamaExecutionRequest] = []
    generated_response = "RT-017 generated response."

    async def fake_execute(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        requests.append(request)
        return OllamaExecutionResult(
            model=request.dispatch_plan.model,
            response_text=generated_response,
        )

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fake_execute,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        context = application.state.runtime_context
        matching_routes = tuple(
            route
            for route in context.ruleset.routes
            if (
                route.enabled
                and route.result.profile == expected_profile
            )
        )
        assert len(matching_routes) == 1
        official_route = matching_routes[0]
        official_profile = (
            context.profile_registry.get(
                expected_profile
            )
        )

        response = client.post(
            "/v1/prompt",
            json={"message": message},
        )

    assert response.status_code == 200
    assert len(requests) == 1

    execution_request = requests[0]
    dispatch_plan = execution_request.dispatch_plan

    assert isinstance(
        execution_request,
        OllamaExecutionRequest,
    )
    assert isinstance(dispatch_plan, DispatchPlan)
    assert execution_request.user_prompt == message
    assert dispatch_plan.profile_id == expected_profile
    assert dispatch_plan.source_state.value == expected_state
    assert dispatch_plan.route_id == official_route.id
    assert dispatch_plan.model == official_profile.model

    assert response.json() == {
        "response": generated_response,
        "profile": expected_profile,
        "model": official_profile.model,
        "state": expected_state,
        "route_id": official_route.id,
    }

    serialized = response.text
    assert dispatch_plan.system_prompt not in serialized
    assert dispatch_plan.registry_hash not in serialized
    assert context.ruleset.ruleset_hash not in serialized
    assert "system_prompt" not in serialized
    assert "registry_hash" not in serialized
    assert "ruleset_hash" not in serialized
    assert "comparison_score" not in serialized
    assert "scoring" not in serialized
    assert "reason" not in serialized
    assert "conflict_resolved" not in serialized
    assert "dispatch_plan" not in serialized


def test_official_prompt_returns_unrouted_without_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fail_if_executed(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        nonlocal calls
        calls += 1
        raise AssertionError("unrouted request must not execute ollama")

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fail_if_executed,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "Corrija este código."},
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "UNROUTED",
            "message": "The request could not be routed.",
        }
    }
    assert calls == 0


def test_official_prompt_rejects_invalid_explicit_profile_without_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fail_if_executed(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        nonlocal calls
        calls += 1
        raise AssertionError("invalid profile must not execute ollama")

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fail_if_executed,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.post(
            "/v1/prompt",
            json={
                "message": "message",
                "explicit_profile": "missing-profile",
            },
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "INVALID_PROFILE",
            "message": (
                "The explicit profile is invalid or disabled."
            ),
        }
    }
    assert calls == 0


@pytest.mark.parametrize(
    ("error_code", "expected_status", "public_code", "public_message"),
    [
        (
            OllamaExecutionErrorCode.NETWORK_ERROR,
            503,
            "MODEL_SERVICE_UNAVAILABLE",
            "The model service is unavailable.",
        ),
        (
            OllamaExecutionErrorCode.INVALID_RESPONSE,
            502,
            "MODEL_SERVICE_ERROR",
            "The model service failed to complete the request.",
        ),
    ],
)
def test_official_prompt_returns_safe_model_service_errors(
    monkeypatch: pytest.MonkeyPatch,
    error_code: OllamaExecutionErrorCode,
    expected_status: int,
    public_code: str,
    public_message: str,
) -> None:
    calls = 0
    internal_message = "SENSITIVE_UPSTREAM_MESSAGE"
    internal_cause = RuntimeError("SENSITIVE_UPSTREAM_CAUSE")

    async def fail_execution(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        nonlocal calls
        calls += 1
        raise OllamaExecutionError(
            code=error_code,
            stage=OllamaExecutionStage.TRANSPORT,
            message=internal_message,
            status_code=418,
            cause=internal_cause,
        )

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fail_execution,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.post(
            "/v1/prompt",
            json={
                "message": "Meu Rigidbody não funciona.",
                "explicit_profile": "mobile-dev",
            },
        )

    assert response.status_code == expected_status
    assert response.json() == {
        "error": {
            "code": public_code,
            "message": public_message,
        }
    }
    assert calls == 1
    assert internal_message not in response.text
    assert "SENSITIVE_UPSTREAM_CAUSE" not in response.text
    assert "418" not in response.text


def test_official_prompt_responses_expose_no_dispatch_internals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_plan: list[DispatchPlan] = []

    async def fake_execute(
        self: OllamaExecutor,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        captured_plan.append(request.dispatch_plan)
        return OllamaExecutionResult(
            model=request.dispatch_plan.model,
            response_text="Public response.",
        )

    monkeypatch.setattr(
        OllamaExecutor,
        "execute",
        fake_execute,
    )
    application = create_app(ROOT)

    with TestClient(application) as client:
        response = client.post(
            "/v1/prompt",
            json={
                "message": "Meu Rigidbody não funciona.",
                "explicit_profile": "mobile-dev",
            },
        )

    assert response.status_code == 200
    assert len(captured_plan) == 1
    plan = captured_plan[0]
    serialized = response.text
    assert plan.system_prompt not in serialized
    assert plan.registry_hash not in serialized
    assert "system_prompt" not in serialized
    assert "registry_hash" not in serialized
    assert "SENSITIVE" not in serialized
