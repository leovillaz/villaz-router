from typing import Any

import pytest
from pydantic import ValidationError

from villaz_router.http_api.models import (
    LivenessResponse,
    PromptRequest,
    PromptResponse,
    ReadinessResponse,
    AmbiguousCandidate,
    ErrorEnvelope,
    ErrorResponse,
)


@pytest.mark.parametrize(
    "model_type",
    [
        LivenessResponse,
        ReadinessResponse,
    ],
)
def test_health_response_has_exact_fields(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
) -> None:
    assert set(model_type.model_fields) == {"status"}
    assert model_type.model_config["extra"] == "forbid"
    assert model_type.model_config["frozen"] is True


def test_liveness_response_has_exact_payload() -> None:
    response = LivenessResponse()

    assert response.status == "alive"
    assert response.model_dump(mode="json") == {
        "status": "alive",
    }


def test_readiness_response_has_exact_payload() -> None:
    response = ReadinessResponse()

    assert response.status == "ready"
    assert response.model_dump(mode="json") == {
        "status": "ready",
    }

def test_readiness_response_accepts_not_ready() -> None:
    response = ReadinessResponse(
        status="not_ready",
    )

    assert response.model_dump(mode="json") == {
        "status": "not_ready",
    }


def test_ambiguous_error_requires_candidates() -> None:
    with pytest.raises(ValidationError):
        ErrorEnvelope(
            code="AMBIGUOUS_ROUTE",
            message=(
                "The request matches multiple routes."
            ),
        )


def test_ambiguous_error_requires_two_candidates() -> None:
    candidate = AmbiguousCandidate(
        route_id="ROUTE-UNITY-001",
        profile="unity-dev",
        comparison_score=20,
    )

    with pytest.raises(ValidationError):
        ErrorEnvelope(
            code="AMBIGUOUS_ROUTE",
            message=(
                "The request matches multiple routes."
            ),
            candidates=(candidate,),
        )


def test_non_ambiguous_error_forbids_candidates() -> None:
    first = AmbiguousCandidate(
        route_id="ROUTE-UNITY-001",
        profile="unity-dev",
        comparison_score=20,
    )
    second = AmbiguousCandidate(
        route_id="ROUTE-MOBILE-001",
        profile="mobile-dev",
        comparison_score=18,
    )

    with pytest.raises(ValidationError):
        ErrorEnvelope(
            code="UNROUTED",
            message=(
                "The request could not be routed."
            ),
            candidates=(
                first,
                second,
            ),
        )

@pytest.mark.parametrize(
    ("model_type", "status"),
    [
        (LivenessResponse, "alive"),
        (ReadinessResponse, "ready"),
    ],
)
def test_health_response_is_frozen(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
    status: str,
) -> None:
    response = model_type.model_validate({"status": status})

    with pytest.raises(ValidationError):
        response.status = "changed"


@pytest.mark.parametrize(
    ("model_type", "status"),
    [
        (LivenessResponse, "alive"),
        (ReadinessResponse, "ready"),
    ],
)
def test_health_response_forbids_extra_fields(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
    status: str,
) -> None:
    with pytest.raises(ValidationError):
        model_type.model_validate({
            "status": status,
            "unexpected": True,
        })


@pytest.mark.parametrize(
    ("model_type", "invalid_status"),
    [
        (LivenessResponse, "ready"),
        (ReadinessResponse, "alive"),
        (LivenessResponse, 1),
        (ReadinessResponse, None),
    ],
)
def test_health_response_rejects_invalid_status(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
    invalid_status: Any,
) -> None:
    with pytest.raises(ValidationError):
        model_type.model_validate({
            "status": invalid_status,
        })

def test_prompt_request_has_exact_contract() -> None:
    assert set(PromptRequest.model_fields) == {
        "message",
        "explicit_profile",
    }
    assert PromptRequest.model_config["extra"] == "forbid"
    assert PromptRequest.model_config["frozen"] is True
    assert PromptRequest.model_config["strict"] is True
    assert (
        PromptRequest.model_config[
            "str_strip_whitespace"
        ]
        is False
    )


def test_prompt_request_preserves_exact_input() -> None:
    request = PromptRequest(
        message="  Meu Rigidbody está irregular.  ",
        explicit_profile=" unity-dev ",
    )

    assert request.message == (
        "  Meu Rigidbody está irregular.  "
    )
    assert request.explicit_profile == " unity-dev "


def test_prompt_request_allows_absent_profile() -> None:
    request = PromptRequest(
        message="Mensagem válida",
    )

    assert request.explicit_profile is None


@pytest.mark.parametrize(
    "invalid_message",
    [
        "",
        " ",
        "\t",
        "\n",
        " \t\n ",
    ],
)
def test_prompt_request_rejects_empty_or_whitespace_message(
    invalid_message: str,
) -> None:
    with pytest.raises(ValidationError):
        PromptRequest(
            message=invalid_message,
        )


@pytest.mark.parametrize(
    "invalid_profile",
    [
        "",
        " ",
        "\t",
        "\n",
        " \t\n ",
    ],
)
def test_prompt_request_rejects_empty_or_whitespace_profile(
    invalid_profile: str,
) -> None:
    with pytest.raises(ValidationError):
        PromptRequest(
            message="Mensagem válida",
            explicit_profile=invalid_profile,
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("message", 1),
        ("message", True),
        ("message", None),
        ("explicit_profile", 1),
        ("explicit_profile", True),
    ],
)
def test_prompt_request_requires_strict_strings(
    field_name: str,
    invalid_value: Any,
) -> None:
    payload: dict[str, Any] = {
        "message": "Mensagem válida",
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        PromptRequest.model_validate(payload)


def test_prompt_request_rejects_message_over_limit() -> None:
    with pytest.raises(ValidationError):
        PromptRequest(
            message="a" * 16_385,
        )


def test_prompt_request_accepts_message_at_limit() -> None:
    request = PromptRequest(
        message="a" * 16_384,
    )

    assert len(request.message) == 16_384


def test_prompt_request_rejects_profile_over_limit() -> None:
    with pytest.raises(ValidationError):
        PromptRequest(
            message="Mensagem válida",
            explicit_profile="a" * 129,
        )


def test_prompt_request_accepts_profile_at_limit() -> None:
    request = PromptRequest(
        message="Mensagem válida",
        explicit_profile="a" * 128,
    )

    assert len(request.explicit_profile or "") == 128


def test_prompt_request_forbids_client_control_fields() -> None:
    forbidden_fields = (
        "model",
        "system",
        "system_prompt",
        "prompt_template",
        "temperature",
        "stream",
        "raw",
        "think",
        "ollama_url",
        "base_url",
    )

    for field_name in forbidden_fields:
        with pytest.raises(ValidationError):
            PromptRequest.model_validate({
                "message": "Mensagem válida",
                field_name: "forbidden",
            })


def test_prompt_request_is_frozen() -> None:
    request = PromptRequest(
        message="Mensagem válida",
    )

    with pytest.raises(ValidationError):
        request.message = "alterada"

def test_prompt_response_has_exact_contract() -> None:
    assert set(PromptResponse.model_fields) == {
        "response",
        "profile",
        "model",
        "state",
        "route_id",
    }
    assert PromptResponse.model_config["extra"] == "forbid"
    assert PromptResponse.model_config["frozen"] is True
    assert PromptResponse.model_config["strict"] is True
    assert (
        PromptResponse.model_config[
            "str_strip_whitespace"
        ]
        is False
    )


@pytest.mark.parametrize(
    ("state", "route_id"),
    [
        ("explicit", None),
        ("routed", "ROUTE-UNITY-001"),
    ],
)
def test_prompt_response_accepts_valid_state_contract(
    state: str,
    route_id: str | None,
) -> None:
    response = PromptResponse(
        response="Resposta do modelo",
        profile="unity-dev",
        model="modelo-local",
        state=state,
        route_id=route_id,
    )

    assert response.state == state
    assert response.route_id == route_id


def test_prompt_response_preserves_exact_response_text() -> None:
    response = PromptResponse(
        response="  resposta exata  ",
        profile="unity-dev",
        model="modelo-local",
        state="explicit",
        route_id=None,
    )

    assert response.response == "  resposta exata  "


@pytest.mark.parametrize(
    "field_name",
    [
        "response",
        "profile",
        "model",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_prompt_response_rejects_empty_required_text(
    field_name: str,
    invalid_value: str,
) -> None:
    payload: dict[str, Any] = {
        "response": "Resposta",
        "profile": "unity-dev",
        "model": "modelo-local",
        "state": "explicit",
        "route_id": None,
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        PromptResponse.model_validate(payload)

def test_prompt_response_rejects_whitespace_route_id() -> None:
    with pytest.raises(ValidationError):
        PromptResponse(
            response="Resposta",
            profile="unity-dev",
            model="modelo-local",
            state="routed",
            route_id=" ",
        )

def test_prompt_response_requires_route_for_routed() -> None:
    with pytest.raises(ValidationError):
        PromptResponse(
            response="Resposta",
            profile="unity-dev",
            model="modelo-local",
            state="routed",
            route_id=None,
        )

def test_prompt_response_forbids_route_for_explicit() -> None:
    with pytest.raises(ValidationError):
        PromptResponse(
            response="Resposta",
            profile="unity-dev",
            model="modelo-local",
            state="explicit",
            route_id="ROUTE-UNITY-001",
        )

@pytest.mark.parametrize(
    "invalid_state",
    [
        "ambiguous",
        "unrouted",
        "manual",
        "",
    ],
)
def test_prompt_response_rejects_non_success_state(
    invalid_state: str,
) -> None:
    with pytest.raises(ValidationError):
        PromptResponse(
            response="Resposta",
            profile="unity-dev",
            model="modelo-local",
            state=invalid_state,
            route_id=None,
        )


def test_prompt_response_forbids_internal_fields() -> None:
    forbidden_fields = (
        "system_prompt",
        "registry_hash",
        "configuration_root",
        "base_url",
        "timeouts",
        "limits",
        "prompt",
        "raw_response",
    )

    for field_name in forbidden_fields:
        with pytest.raises(ValidationError):
            PromptResponse.model_validate({
                "response": "Resposta",
                "profile": "unity-dev",
                "model": "modelo-local",
                "state": "explicit",
                "route_id": None,
                field_name: "forbidden",
            })


def test_prompt_response_is_frozen() -> None:
    response = PromptResponse(
        response="Resposta",
        profile="unity-dev",
        model="modelo-local",
        state="explicit",
        route_id=None,
    )

    with pytest.raises(ValidationError):
        response.response = "alterada"

def test_ambiguous_candidate_has_exact_contract() -> None:
    assert set(AmbiguousCandidate.model_fields) == {
        "route_id",
        "profile",
        "comparison_score",
    }
    assert (
        AmbiguousCandidate.model_config["extra"]
        == "forbid"
    )
    assert (
        AmbiguousCandidate.model_config["frozen"]
        is True
    )
    assert (
        AmbiguousCandidate.model_config["strict"]
        is True
    )


def test_ambiguous_candidate_accepts_valid_values() -> None:
    candidate = AmbiguousCandidate(
        route_id="ROUTE-UNITY-001",
        profile="unity-dev",
        comparison_score=20,
    )

    assert candidate.model_dump() == {
        "route_id": "ROUTE-UNITY-001",
        "profile": "unity-dev",
        "comparison_score": 20,
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "route_id",
        "profile",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_ambiguous_candidate_rejects_empty_text(
    field_name: str,
    invalid_value: str,
) -> None:
    payload: dict[str, Any] = {
        "route_id": "ROUTE-UNITY-001",
        "profile": "unity-dev",
        "comparison_score": 20,
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        AmbiguousCandidate.model_validate(payload)


@pytest.mark.parametrize(
    "invalid_score",
    [
        -1,
        1.0,
        "1",
        True,
    ],
)
def test_ambiguous_candidate_requires_nonnegative_strict_int(
    invalid_score: Any,
) -> None:
    with pytest.raises(ValidationError):
        AmbiguousCandidate(
            route_id="ROUTE-UNITY-001",
            profile="unity-dev",
            comparison_score=invalid_score,
        )


def test_error_envelope_has_exact_contract() -> None:
    assert set(ErrorEnvelope.model_fields) == {
        "code",
        "message",
        "candidates",
    }
    assert ErrorEnvelope.model_config["extra"] == "forbid"
    assert ErrorEnvelope.model_config["frozen"] is True
    assert ErrorEnvelope.model_config["strict"] is True


def test_unrouted_error_envelope_has_exact_payload() -> None:
    envelope = ErrorEnvelope(
        code="UNROUTED",
        message="The request could not be routed.",
    )

    assert envelope.model_dump(
        mode="json",
        exclude_none=True,
    ) == {
        "code": "UNROUTED",
        "message": "The request could not be routed.",
    }


def test_ambiguous_error_preserves_candidate_order() -> None:
    first = AmbiguousCandidate(
        route_id="ROUTE-UNITY-001",
        profile="unity-dev",
        comparison_score=20,
    )
    second = AmbiguousCandidate(
        route_id="ROUTE-MOBILE-001",
        profile="mobile-dev",
        comparison_score=18,
    )

    envelope = ErrorEnvelope(
        code="AMBIGUOUS_ROUTE",
        message=(
            "The request matches multiple routes."
        ),
        candidates=(
            first,
            second,
        ),
    )

    assert envelope.candidates == (
        first,
        second,
    )


def test_error_envelope_does_not_reorder_candidates() -> None:
    first = AmbiguousCandidate(
        route_id="ROUTE-B",
        profile="profile-b",
        comparison_score=10,
    )
    second = AmbiguousCandidate(
        route_id="ROUTE-A",
        profile="profile-a",
        comparison_score=20,
    )

    envelope = ErrorEnvelope(
        code="AMBIGUOUS_ROUTE",
        message=(
            "The request matches multiple routes."
        ),
        candidates=(
            first,
            second,
        ),
    )

    assert envelope.candidates == (
        first,
        second,
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "code",
        "message",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_error_envelope_rejects_empty_text(
    field_name: str,
    invalid_value: str,
) -> None:
    payload: dict[str, Any] = {
        "code": "UNROUTED",
        "message": "The request could not be routed.",
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        ErrorEnvelope.model_validate(payload)


def test_error_response_has_exact_contract() -> None:
    assert set(ErrorResponse.model_fields) == {
        "error",
    }
    assert ErrorResponse.model_config["extra"] == "forbid"
    assert ErrorResponse.model_config["frozen"] is True
    assert ErrorResponse.model_config["strict"] is True


def test_error_response_has_common_public_shape() -> None:
    response = ErrorResponse(
        error=ErrorEnvelope(
            code="INVALID_REQUEST",
            message="The request is invalid.",
        )
    )

    assert response.model_dump(
        mode="json",
        exclude_none=True,
    ) == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "The request is invalid.",
        }
    }


def test_error_models_forbid_internal_fields() -> None:
    forbidden_fields = (
        "system_prompt",
        "registry_hash",
        "configuration_root",
        "base_url",
        "traceback",
        "details",
        "prompt",
        "response_text",
    )

    for field_name in forbidden_fields:
        with pytest.raises(ValidationError):
            ErrorEnvelope.model_validate({
                "code": "INTERNAL_ERROR",
                "message": "Internal error.",
                field_name: "forbidden",
            })
