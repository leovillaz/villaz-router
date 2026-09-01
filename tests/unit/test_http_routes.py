import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import villaz_router.http_api.routes as routes_module
from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.dispatcher_errors import (
    DispatcherError,
    DispatcherErrorCode,
)
from villaz_router.dispatcher_models import DispatchPlan
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.http_api.dependencies import (
    get_ollama_executor,
    get_runtime_context,
)
from villaz_router.http_api.models import (
    AmbiguousCandidate,
    ErrorEnvelope,
    ErrorResponse,
    LivenessResponse,
    PromptRequest,
    PromptResponse,
    ReadinessResponse,
)
from villaz_router.http_api.router_adapter import HttpRoutingError
from villaz_router.http_api.routes import router

from villaz_router.models import (
    RouteDecision,
    RouteState,
    RoutingMode,
    RoutingReason,
    RulesetSnapshot,
)
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
from villaz_router.registry_errors import (
    RegistryError,
    RegistryErrorCode,
)
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)


def make_runtime_context(root: Path) -> RuntimeContext:
    return RuntimeContext.model_construct(
        configuration_root=root,
        ruleset=RulesetSnapshot.model_construct(),
        profile_registry=(
            ProfileRegistrySnapshot.model_construct()
        ),
    )

class FakeOllamaTransport:
    async def generate(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        raise AssertionError(
            "readiness must not execute ollama"
        )

    async def aclose(self) -> None:
        return None


def make_ollama_executor() -> OllamaExecutor:
    return OllamaExecutor(
        FakeOllamaTransport()
    )

def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def make_prompt_runtime_context(root: Path) -> RuntimeContext:
    profile = ProfileDefinition(
        id="mobile-dev",
        enabled=True,
        display_name="Mobile Dev",
        description="Mobile development profile",
        model="qwen3:8b",
        system_prompt="SENSITIVE_SYSTEM_PROMPT",
    )
    registry = ProfileRegistrySnapshot(
        profiles=(profile,),
        profile_ids=(profile.id,),
        registry_hash="a" * 64,
    )
    return RuntimeContext.model_construct(
        configuration_root=root,
        ruleset=RulesetSnapshot.model_construct(),
        profile_registry=registry,
    )


def make_route_decision(
    state: RouteState = RouteState.ROUTED,
) -> RouteDecision:
    return RouteDecision(
        state=state,
        profile="mobile-dev",
        route_id=(
            "ROUTE-MOBILE-001"
            if state is RouteState.ROUTED
            else None
        ),
        comparison_score=(
            10
            if state is RouteState.ROUTED
            else None
        ),
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


def make_dispatch_plan(
    state: RouteState = RouteState.ROUTED,
) -> DispatchPlan:
    return DispatchPlan(
        profile_id="mobile-dev",
        model="qwen3:8b",
        system_prompt="SENSITIVE_SYSTEM_PROMPT",
        registry_hash="b" * 64,
        source_state=state,
        route_id=(
            "ROUTE-MOBILE-001"
            if state is RouteState.ROUTED
            else None
        ),
    )


class RecordingOllamaExecutor:
    def __init__(
        self,
        result: OllamaExecutionResult | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.result = result or OllamaExecutionResult(
            model="qwen3:8b",
            response_text="Generated response.",
        )
        self.error = error
        self.requests: list[OllamaExecutionRequest] = []

    async def execute(
        self,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.result


def make_prompt_app(
    runtime_context: RuntimeContext,
    executor: RecordingOllamaExecutor,
) -> FastAPI:
    app = make_app()
    app.dependency_overrides[get_runtime_context] = (
        lambda: runtime_context
    )
    app.dependency_overrides[get_ollama_executor] = (
        lambda: executor
    )
    return app


def test_router_has_exact_routes_and_methods() -> None:
    routes_by_path = {
        route.path: route
        for route in router.routes
    }

    assert set(routes_by_path) == {
        "/health/live",
        "/health/ready",
        "/v1/prompt",
    }

    live_route = routes_by_path["/health/live"]
    ready_route = routes_by_path["/health/ready"]
    prompt_route = routes_by_path["/v1/prompt"]

    assert live_route.methods == {"GET"}
    assert ready_route.methods == {"GET"}
    assert prompt_route.methods == {"POST"}
    assert live_route.response_model is LivenessResponse
    assert ready_route.response_model is ReadinessResponse
    assert prompt_route.response_model is PromptResponse


def test_liveness_returns_exact_response_without_context() -> None:
    app = make_app()
    app.state.runtime_context = "invalid"

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
    }


def test_readiness_returns_ready_with_valid_state(
    tmp_path: Path,
) -> None:
    app = make_app()
    app.state.runtime_context = (
        make_runtime_context(
            tmp_path.resolve()
        )
    )
    app.state.ollama_executor = (
        make_ollama_executor()
    )

    with TestClient(app) as client:
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }

def test_readiness_returns_not_ready_without_runtime_context() -> None:
    app = make_app()
    app.state.ollama_executor = (
        make_ollama_executor()
    )

    with TestClient(app) as client:
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
    }


def test_readiness_returns_not_ready_without_ollama_executor(
    tmp_path: Path,
) -> None:
    app = make_app()
    app.state.runtime_context = (
        make_runtime_context(
            tmp_path.resolve()
        )
    )

    with TestClient(app) as client:
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
    }


@pytest.mark.parametrize(
    "invalid_context",
    [
        None,
        "invalid",
        object(),
        {},
    ],
)
def test_readiness_returns_not_ready_with_invalid_runtime_context(
    invalid_context: Any,
) -> None:
    app = make_app()
    app.state.runtime_context = invalid_context
    app.state.ollama_executor = (
        make_ollama_executor()
    )

    with TestClient(app) as client:
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
    }


@pytest.mark.parametrize(
    "invalid_executor",
    [
        None,
        "invalid",
        object(),
        {},
    ],
)
def test_readiness_returns_not_ready_with_invalid_ollama_executor(
    tmp_path: Path,
    invalid_executor: Any,
) -> None:
    app = make_app()
    app.state.runtime_context = (
        make_runtime_context(
            tmp_path.resolve()
        )
    )
    app.state.ollama_executor = invalid_executor

    with TestClient(app) as client:
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
    }

@pytest.mark.parametrize(
    "path",
    [
        "/health/live",
        "/health/ready",
    ],
)
def test_health_routes_reject_post(path: str) -> None:
    app = make_app()

    with TestClient(app) as client:
        response = client.post(path)

    assert response.status_code == 405
    assert response.json() == {
        "detail": "Method Not Allowed",
    }


def test_unknown_route_returns_not_found() -> None:
    app = make_app()

    with TestClient(app) as client:
        response = client.get("/unknown")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Not Found",
    }


def test_prompt_adapter_receives_exact_request_and_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    captured: dict[str, object] = {}

    def fake_route_prompt_request(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> HttpRoutingError:
        captured["prompt_request"] = prompt_request
        captured["runtime_context"] = received_context
        return HttpRoutingError(
            status_code=422,
            body=ErrorResponse(
                error=ErrorEnvelope(
                    code="UNROUTED",
                    message="The request could not be routed.",
                )
            ),
        )

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fake_route_prompt_request,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={
                "message": "  Preserve this message exactly.  ",
                "explicit_profile": "  mobile-dev  ",
            },
        )

    prompt_request = captured["prompt_request"]
    assert isinstance(prompt_request, PromptRequest)
    assert prompt_request.message == "  Preserve this message exactly.  "
    assert prompt_request.explicit_profile == "  mobile-dev  "
    assert captured["runtime_context"] is runtime_context
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("status_code", "body"),
    [
        (
            409,
            ErrorResponse(
                error=ErrorEnvelope(
                    code="AMBIGUOUS_ROUTE",
                    message="The request matches multiple routes.",
                    candidates=(
                        AmbiguousCandidate(
                            route_id="route-a",
                            profile="mobile-dev",
                            comparison_score=10,
                        ),
                        AmbiguousCandidate(
                            route_id="route-b",
                            profile="docs-dev",
                            comparison_score=10,
                        ),
                    ),
                )
            ),
        ),
        (
            422,
            ErrorResponse(
                error=ErrorEnvelope(
                    code="UNROUTED",
                    message="The request could not be routed.",
                )
            ),
        ),
        (
            422,
            ErrorResponse(
                error=ErrorEnvelope(
                    code="INVALID_PROFILE",
                    message=(
                        "The explicit profile is invalid or disabled."
                    ),
                )
            ),
        ),
    ],
)
def test_prompt_http_routing_error_stops_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    body: ErrorResponse,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    dispatcher_calls = 0

    def fake_route_prompt_request(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> HttpRoutingError:
        return HttpRoutingError(
            status_code=status_code,
            body=body,
        )

    def fail_dispatcher(
        decision: RouteDecision,
        registry: ProfileRegistrySnapshot,
    ) -> DispatchPlan:
        nonlocal dispatcher_calls
        dispatcher_calls += 1
        raise AssertionError("dispatcher must not be called")

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fake_route_prompt_request,
    )
    monkeypatch.setattr(
        routes_module,
        "build_dispatch_plan",
        fail_dispatcher,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == status_code
    assert response.json() == body.model_dump(
        mode="json",
        exclude_none=True,
    )
    assert dispatcher_calls == 0
    assert executor.requests == []


def test_prompt_pipeline_preserves_object_identity_and_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    dispatch_plan = make_dispatch_plan()
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    captured: dict[str, object] = {}

    def fake_route_prompt_request(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> RouteDecision:
        return decision

    def fake_build_dispatch_plan(
        received_decision: RouteDecision,
        registry: ProfileRegistrySnapshot,
    ) -> DispatchPlan:
        captured["decision"] = received_decision
        captured["registry"] = registry
        return dispatch_plan

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fake_route_prompt_request,
    )
    monkeypatch.setattr(
        routes_module,
        "build_dispatch_plan",
        fake_build_dispatch_plan,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "  Original message.  "},
        )

    assert response.status_code == 200
    assert captured["decision"] is decision
    assert captured["registry"] is runtime_context.profile_registry
    assert len(executor.requests) == 1
    execution_request = executor.requests[0]
    assert execution_request.dispatch_plan is dispatch_plan
    assert execution_request.user_prompt == "  Original message.  "


@pytest.mark.parametrize(
    ("state", "expected_route_id"),
    [
        (RouteState.EXPLICIT, None),
        (RouteState.ROUTED, "ROUTE-MOBILE-001"),
    ],
)
def test_prompt_success_returns_exact_public_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: RouteState,
    expected_route_id: str | None,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision(state)
    dispatch_plan = make_dispatch_plan(state)
    executor = RecordingOllamaExecutor(
        result=OllamaExecutionResult(
            model="qwen3:8b",
            response_text="Public generated response.",
        )
    )
    app = make_prompt_app(runtime_context, executor)

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        lambda prompt_request, received_context: decision,
    )
    monkeypatch.setattr(
        routes_module,
        "build_dispatch_plan",
        lambda received_decision, registry: dispatch_plan,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Public generated response.",
        "profile": "mobile-dev",
        "model": "qwen3:8b",
        "state": state.value,
        "route_id": expected_route_id,
    }
    serialized = response.text
    assert "SENSITIVE_SYSTEM_PROMPT" not in serialized
    assert dispatch_plan.registry_hash not in serialized
    assert "comparison_score" not in serialized
    assert "raw" not in serialized
    assert len(executor.requests) == 1


@pytest.mark.parametrize(
    "error_code",
    list(DispatcherErrorCode),
)
def test_all_dispatcher_errors_return_safe_internal_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_code: DispatcherErrorCode,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    internal_message = "SENSITIVE_DISPATCHER_MESSAGE"

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        lambda prompt_request, received_context: decision,
    )

    def fail_dispatcher(
        received_decision: RouteDecision,
        registry: ProfileRegistrySnapshot,
    ) -> DispatchPlan:
        raise DispatcherError(error_code, internal_message)

    monkeypatch.setattr(
        routes_module,
        "build_dispatch_plan",
        fail_dispatcher,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": (
                "The request could not be completed due to an internal error."
            ),
        }
    }
    assert internal_message not in response.text
    assert executor.requests == []


@pytest.mark.parametrize(
    "error_code",
    [
        RouterErrorCode.INVALID_RULESET,
        RouterErrorCode.INVALID_SCORING_INPUT,
    ],
)
def test_propagated_router_error_returns_safe_internal_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_code: RouterErrorCode,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    internal_message = "SENSITIVE_ROUTER_MESSAGE"

    def fail_router(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> RouteDecision:
        raise RouterError(error_code, internal_message)

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fail_router,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "INTERNAL_ERROR",
        "message": (
            "The request could not be completed due to an internal error."
        ),
    }
    assert internal_message not in response.text
    assert executor.requests == []


def test_unexpected_registry_error_returns_safe_internal_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    internal_message = "SENSITIVE_REGISTRY_MESSAGE"

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        lambda prompt_request, received_context: decision,
    )

    def fail_dispatcher(
        received_decision: RouteDecision,
        registry: ProfileRegistrySnapshot,
    ) -> DispatchPlan:
        raise RegistryError(
            RegistryErrorCode.INVALID_REGISTRY,
            internal_message,
        )

    monkeypatch.setattr(
        routes_module,
        "build_dispatch_plan",
        fail_dispatcher,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert internal_message not in response.text
    assert executor.requests == []


@pytest.mark.parametrize(
    ("error_code", "expected_status", "public_code", "public_message"),
    [
        *[
            (
                code,
                504,
                "MODEL_SERVICE_TIMEOUT",
                "The model service timed out.",
            )
            for code in (
                OllamaExecutionErrorCode.CONNECT_TIMEOUT,
                OllamaExecutionErrorCode.READ_TIMEOUT,
                OllamaExecutionErrorCode.WRITE_TIMEOUT,
            )
        ],
        *[
            (
                code,
                503,
                "MODEL_SERVICE_UNAVAILABLE",
                "The model service is unavailable.",
            )
            for code in (
                OllamaExecutionErrorCode.POOL_TIMEOUT,
                OllamaExecutionErrorCode.NETWORK_ERROR,
            )
        ],
        *[
            (
                code,
                502,
                "MODEL_SERVICE_ERROR",
                "The model service failed to complete the request.",
            )
            for code in (
                OllamaExecutionErrorCode.PROTOCOL_ERROR,
                OllamaExecutionErrorCode.HTTP_STATUS_ERROR,
                OllamaExecutionErrorCode.INVALID_JSON_RESPONSE,
                OllamaExecutionErrorCode.INVALID_RESPONSE,
                OllamaExecutionErrorCode.MODEL_MISMATCH,
                OllamaExecutionErrorCode.EMPTY_RESPONSE,
                OllamaExecutionErrorCode.GENERATION_INCOMPLETE,
            )
        ],
        (
            OllamaExecutionErrorCode.INVALID_EXECUTION_RESULT,
            500,
            "INTERNAL_ERROR",
            "The request could not be completed due to an internal error.",
        ),
    ],
)
def test_all_ollama_errors_use_frozen_safe_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_code: OllamaExecutionErrorCode,
    expected_status: int,
    public_code: str,
    public_message: str,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    internal_cause = RuntimeError("SENSITIVE_OLLAMA_CAUSE")
    executor = RecordingOllamaExecutor(
        error=OllamaExecutionError(
            code=error_code,
            stage=OllamaExecutionStage.TRANSPORT,
            message="SENSITIVE_OLLAMA_MESSAGE",
            status_code=418,
            cause=internal_cause,
        )
    )
    app = make_prompt_app(runtime_context, executor)

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        lambda prompt_request, received_context: decision,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == expected_status
    assert response.json() == {
        "error": {
            "code": public_code,
            "message": public_message,
        }
    }
    assert "SENSITIVE_OLLAMA_MESSAGE" not in response.text
    assert "SENSITIVE_OLLAMA_CAUSE" not in response.text
    assert "418" not in response.text
    assert len(executor.requests) == 1


def test_http_status_error_never_replicates_upstream_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    executor = RecordingOllamaExecutor(
        error=OllamaExecutionError(
            code=OllamaExecutionErrorCode.HTTP_STATUS_ERROR,
            stage=OllamaExecutionStage.HTTP_RESPONSE,
            message="upstream returned 429",
            status_code=429,
        )
    )
    app = make_prompt_app(runtime_context, executor)
    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        lambda prompt_request, received_context: decision,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 502
    assert "429" not in response.text
    assert len(executor.requests) == 1


def test_unexpected_error_inside_prompt_returns_safe_internal_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    internal_message = "SENSITIVE_UNEXPECTED_FAILURE"

    def fail_router(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> RouteDecision:
        raise RuntimeError(internal_message)

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fail_router,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert internal_message not in response.text
    assert executor.requests == []


def test_ollama_failure_is_not_retried_or_fallbacked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    executor = RecordingOllamaExecutor(
        error=OllamaExecutionError(
            code=OllamaExecutionErrorCode.NETWORK_ERROR,
            stage=OllamaExecutionStage.TRANSPORT,
            message="network failed",
        )
    )
    app = make_prompt_app(runtime_context, executor)
    adapter_calls = 0
    dispatcher_calls = 0

    def fake_router(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> RouteDecision:
        nonlocal adapter_calls
        adapter_calls += 1
        return decision

    def fake_dispatcher(
        received_decision: RouteDecision,
        registry: ProfileRegistrySnapshot,
    ) -> DispatchPlan:
        nonlocal dispatcher_calls
        dispatcher_calls += 1
        return make_dispatch_plan()

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fake_router,
    )
    monkeypatch.setattr(
        routes_module,
        "build_dispatch_plan",
        fake_dispatcher,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json={"message": "message"},
        )

    assert response.status_code == 503
    assert adapter_calls == 1
    assert dispatcher_calls == 1
    assert len(executor.requests) == 1


@pytest.mark.anyio
async def test_prompt_cancellation_propagates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    decision = make_route_decision()
    cancellation = asyncio.CancelledError()
    executor = RecordingOllamaExecutor(error=cancellation)
    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        lambda prompt_request, received_context: decision,
    )

    with pytest.raises(asyncio.CancelledError) as exc_info:
        await routes_module.post_prompt(
            PromptRequest(message="message"),
            runtime_context,
            executor,
        )

    assert exc_info.value is cancellation
    assert len(executor.requests) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"message": ""},
        {"message": "a" * 16_385},
        {
            "message": "message",
            "explicit_profile": "a" * 129,
        },
    ],
)
def test_prompt_validation_stays_422_before_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> None:
    runtime_context = make_prompt_runtime_context(tmp_path)
    executor = RecordingOllamaExecutor()
    app = make_prompt_app(runtime_context, executor)
    adapter_calls = 0

    def fail_if_routed(
        prompt_request: PromptRequest,
        received_context: RuntimeContext,
    ) -> RouteDecision:
        nonlocal adapter_calls
        adapter_calls += 1
        raise AssertionError("invalid request reached pipeline")

    monkeypatch.setattr(
        routes_module,
        "route_prompt_request",
        fail_if_routed,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/prompt",
            json=payload,
        )

    assert response.status_code == 422
    assert "detail" in response.json()
    assert adapter_calls == 0
    assert executor.requests == []
