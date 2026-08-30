from collections.abc import Mapping
from pathlib import Path

import pytest

from villaz_router import (
    DispatchPlan,
    RouteRequest,
    RouteState,
    bootstrap_runtime,
    build_dispatch_plan,
    decide_route,
)
from villaz_router.ollama_execution import (
    OllamaExecutionRequest,
    OllamaExecutionResult,
    OllamaExecutor,
    OllamaTransport,
)


ROOT = Path(__file__).resolve().parents[2]

USER_PROMPT = (
    "Meu Rigidbody está se movimentando de forma irregular."
)

EXPECTED_PROFILE = "unity-dev"
EXPECTED_ROUTE_ID = "ROUTE-UNITY-001"

EXPECTED_PAYLOAD_KEYS = {
    "model",
    "system",
    "prompt",
    "stream",
    "raw",
    "think",
}

FAKE_RESPONSE_TEXT = "resposta sintética do transporte falso"


class InspectingFakeOllamaTransport:
    def __init__(
        self,
        dispatch_plan: DispatchPlan,
        user_prompt: str,
    ) -> None:
        self._dispatch_plan = dispatch_plan
        self._user_prompt = user_prompt
        self.generate_calls = 0
        self.close_calls = 0
        self.payload_validated = False

    async def generate(
        self,
        payload: Mapping[str, object],
    ) -> object:
        self.generate_calls += 1

        if set(payload) != EXPECTED_PAYLOAD_KEYS:
            raise AssertionError(
                "ollama payload keys do not match the exact contract"
            )

        if payload["model"] != self._dispatch_plan.model:
            raise AssertionError(
                "dispatch model changed before reaching transport"
            )

        if payload["system"] != self._dispatch_plan.system_prompt:
            raise AssertionError(
                "system prompt changed before reaching transport"
            )

        if payload["prompt"] != self._user_prompt:
            raise AssertionError(
                "user prompt changed before reaching transport"
            )

        if payload["stream"] is not False:
            raise AssertionError(
                "stream must be exactly false"
            )

        if payload["raw"] is not False:
            raise AssertionError(
                "raw must be exactly false"
            )

        if payload["think"] is not False:
            raise AssertionError(
                "think must be exactly false"
            )

        self.payload_validated = True

        return {
            "model": self._dispatch_plan.model,
            "response": FAKE_RESPONSE_TEXT,
            "done": True,
        }

    async def aclose(self) -> None:
        self.close_calls += 1


@pytest.mark.anyio
async def test_official_route_reaches_ollama_execution_without_network() -> None:
    context = bootstrap_runtime(ROOT)

    routing_request = RouteRequest(
        message=USER_PROMPT,
        explicit_profile=None,
    )

    decision = decide_route(
        routing_request,
        context.ruleset,
    )

    assert decision.state is RouteState.ROUTED
    assert decision.profile == EXPECTED_PROFILE
    assert decision.route_id == EXPECTED_ROUTE_ID
    assert decision.conflict_resolved is False

    dispatch_plan = build_dispatch_plan(
        decision,
        context.profile_registry,
    )

    official_profile = context.profile_registry.get(
        EXPECTED_PROFILE
    )

    assert dispatch_plan.profile_id == EXPECTED_PROFILE
    assert dispatch_plan.route_id == EXPECTED_ROUTE_ID
    assert dispatch_plan.model == official_profile.model

    if dispatch_plan.system_prompt != official_profile.system_prompt:
        raise AssertionError(
            "dispatcher did not preserve the official system prompt"
        )

    execution_request = OllamaExecutionRequest(
        dispatch_plan=dispatch_plan,
        user_prompt=USER_PROMPT,
    )

    if execution_request.dispatch_plan is not dispatch_plan:
        raise AssertionError(
            "execution request did not preserve DispatchPlan identity"
        )

    if execution_request.user_prompt != USER_PROMPT:
        raise AssertionError(
            "execution request changed the original user prompt"
        )

    transport = InspectingFakeOllamaTransport(
        dispatch_plan=dispatch_plan,
        user_prompt=USER_PROMPT,
    )

    assert isinstance(transport, OllamaTransport)

    async with OllamaExecutor(transport) as executor:
        result = await executor.execute(
            execution_request
        )

        assert isinstance(result, OllamaExecutionResult)
        assert result.model == dispatch_plan.model
        assert result.response_text == FAKE_RESPONSE_TEXT

        assert transport.generate_calls == 1
        assert transport.payload_validated is True
        assert transport.close_calls == 0

    assert transport.close_calls == 1
