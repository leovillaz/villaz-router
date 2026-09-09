from typing import Any

import pytest
from pydantic import ValidationError

from villaz_router.dispatcher_models import DispatchPlan
from villaz_router.models import RouteState
from villaz_router.ollama_execution.models import (
    OllamaExecutionRequest,
    OllamaExecutionResult,
)


def make_dispatch_plan() -> DispatchPlan:
    return DispatchPlan(
        profile_id="docs-dev",
        model="gemma3:12b",
        system_prompt="Canonical system prompt.",
        registry_hash="a" * 64,
        source_state=RouteState.ROUTED,
        route_id="route-docs",
    )


def make_execution_request() -> OllamaExecutionRequest:
    return OllamaExecutionRequest(
        dispatch_plan=make_dispatch_plan(),
        user_prompt="Explain the architecture.",
    )


def make_execution_result() -> OllamaExecutionResult:
    return OllamaExecutionResult(
        model="gemma3:12b",
        response_text="Architecture explanation.",
        output_tokens=42,
        generation_duration_ns=1_500_000_000,
    )


@pytest.mark.parametrize(
    ("model_type", "expected_fields"),
    [
        (
            OllamaExecutionRequest,
            {
                "dispatch_plan",
                "user_prompt",
            },
        ),
        (
            OllamaExecutionResult,
            {
                "model",
                "response_text",
                "output_tokens",
                "generation_duration_ns",
            },
        ),
    ],
)
def test_execution_models_have_exact_contract(
    model_type: type[
        OllamaExecutionRequest
        | OllamaExecutionResult
    ],
    expected_fields: set[str],
) -> None:
    assert set(model_type.model_fields) == expected_fields
    assert model_type.model_config["extra"] == "forbid"
    assert model_type.model_config["frozen"] is True
    assert model_type.model_config["strict"] is True
    assert (
        model_type.model_config[
            "str_strip_whitespace"
        ]
        is False
    )
    assert all(
        field.is_required()
        for field in model_type.model_fields.values()
    )


def test_execution_request_preserves_values_and_identity() -> None:
    dispatch_plan = make_dispatch_plan()
    user_prompt = (
        "  Explain the architecture exactly.\n"
    )

    request = OllamaExecutionRequest(
        dispatch_plan=dispatch_plan,
        user_prompt=user_prompt,
    )

    assert request.dispatch_plan is dispatch_plan
    assert request.user_prompt == user_prompt
    assert request.model_dump(mode="json") == {
        "dispatch_plan": (
            dispatch_plan.model_dump(mode="json")
        ),
        "user_prompt": user_prompt,
    }


def test_execution_result_preserves_exact_text() -> None:
    model = "  gemma3:12b  "
    response_text = (
        "  Generated response with whitespace.\n"
    )

    result = OllamaExecutionResult(
        model=model,
        response_text=response_text,
        output_tokens=42,
        generation_duration_ns=1_500_000_000,
    )

    assert result.model == model
    assert result.response_text == response_text
    assert result.model_dump(mode="json") == {
        "model": model,
        "response_text": response_text,
        "output_tokens": 42,
        "generation_duration_ns": 1_500_000_000,
    }


@pytest.mark.parametrize(
    ("instance", "field_name", "new_value"),
    [
        (
            make_execution_request(),
            "user_prompt",
            "changed",
        ),
        (
            make_execution_result(),
            "response_text",
            "changed",
        ),
    ],
)
def test_execution_models_are_frozen(
    instance: (
        OllamaExecutionRequest
        | OllamaExecutionResult
    ),
    field_name: str,
    new_value: str,
) -> None:
    with pytest.raises(ValidationError):
        setattr(
            instance,
            field_name,
            new_value,
        )


def test_execution_request_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        OllamaExecutionRequest.model_validate({
            "dispatch_plan": make_dispatch_plan(),
            "user_prompt": "Prompt.",
            "unexpected": True,
        })


def test_execution_result_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        OllamaExecutionResult.model_validate({
            "model": "gemma3:12b",
            "response_text": "Response.",
            "output_tokens": 42,
            "generation_duration_ns": 1_500_000_000,
            "unexpected": True,
        })


def test_execution_request_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        OllamaExecutionRequest.model_validate({
            "dispatch_plan": make_dispatch_plan(),
        })

    with pytest.raises(ValidationError):
        OllamaExecutionRequest.model_validate({
            "user_prompt": "Prompt.",
        })


@pytest.mark.parametrize(
    "missing_field",
    [
        "model",
        "response_text",
        "output_tokens",
        "generation_duration_ns",
    ],
)
def test_execution_result_requires_all_fields(
    missing_field: str,
) -> None:
    values: dict[str, Any] = {
        "model": "gemma3:12b",
        "response_text": "Response.",
        "output_tokens": 42,
        "generation_duration_ns": 1_500_000_000,
    }
    del values[missing_field]

    with pytest.raises(ValidationError):
        OllamaExecutionResult.model_validate(values)

@pytest.mark.parametrize(
    "invalid_dispatch_plan",
    [
        None,
        {},
        "invalid",
        object(),
    ],
)
def test_execution_request_requires_dispatch_plan_instance(
    invalid_dispatch_plan: Any,
) -> None:
    with pytest.raises(ValidationError):
        OllamaExecutionRequest(
            dispatch_plan=invalid_dispatch_plan,
            user_prompt="Prompt.",
        )


@pytest.mark.parametrize(
    "invalid_prompt",
    [
        "",
        " ",
        "\t",
        "\n",
        " \t\n ",
    ],
)
def test_execution_request_rejects_empty_prompt(
    invalid_prompt: str,
) -> None:
    with pytest.raises(ValidationError):
        OllamaExecutionRequest(
            dispatch_plan=make_dispatch_plan(),
            user_prompt=invalid_prompt,
        )


@pytest.mark.parametrize(
    "invalid_prompt",
    [
        1,
        True,
        b"prompt",
        None,
    ],
)
def test_execution_request_requires_exact_string_prompt(
    invalid_prompt: Any,
) -> None:
    with pytest.raises(ValidationError):
        OllamaExecutionRequest(
            dispatch_plan=make_dispatch_plan(),
            user_prompt=invalid_prompt,
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("model", ""),
        ("model", " "),
        ("model", "\t\n"),
        ("response_text", ""),
        ("response_text", " "),
        ("response_text", "\t\n"),
    ],
)
def test_execution_result_rejects_empty_required_text(
    field_name: str,
    invalid_value: str,
) -> None:
    values: dict[str, Any] = {
        "model": "gemma3:12b",
        "response_text": "Response.",
        "output_tokens": 42,
        "generation_duration_ns": 1_500_000_000,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        OllamaExecutionResult.model_validate(values)


@pytest.mark.parametrize(
    "invalid_value",
    [
        1,
        True,
        b"text",
        None,
    ],
)
@pytest.mark.parametrize(
    "field_name",
    [
        "model",
        "response_text",
    ],
)
def test_execution_result_requires_exact_string_types(
    field_name: str,
    invalid_value: Any,
) -> None:
    values: dict[str, Any] = {
        "model": "gemma3:12b",
        "response_text": "Response.",
        "output_tokens": 42,
        "generation_duration_ns": 1_500_000_000,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        OllamaExecutionResult.model_validate(values)

@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("output_tokens", -1),
        ("generation_duration_ns", 0),
        ("generation_duration_ns", -1),
    ],
)
def test_execution_result_rejects_invalid_generation_metrics(
    field_name: str,
    invalid_value: int,
) -> None:
    values: dict[str, Any] = {
        "model": "gemma3:12b",
        "response_text": "Response.",
        "output_tokens": 42,
        "generation_duration_ns": 1_500_000_000,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        OllamaExecutionResult.model_validate(values)

@pytest.mark.parametrize(
    "invalid_value",
    [
        True,
        1.0,
        "42",
        None,
    ],
)
@pytest.mark.parametrize(
    "field_name",
    [
        "output_tokens",
        "generation_duration_ns",
    ],
)
def test_execution_result_requires_exact_integer_metrics(
    field_name: str,
    invalid_value: Any,
) -> None:
    values: dict[str, Any] = {
        "model": "gemma3:12b",
        "response_text": "Response.",
        "output_tokens": 42,
        "generation_duration_ns": 1_500_000_000,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        OllamaExecutionResult.model_validate(values)

def test_execution_result_accepts_zero_output_tokens() -> None:
    result = OllamaExecutionResult(
        model="gemma3:12b",
        response_text="Response.",
        output_tokens=0,
        generation_duration_ns=1,
    )

    assert result.output_tokens == 0
    assert result.generation_duration_ns == 1
