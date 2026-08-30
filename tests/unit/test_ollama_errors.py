from typing import Any

import pytest

from villaz_router.ollama_execution.errors import (
    OllamaExecutionError,
    OllamaExecutionErrorCode,
    OllamaExecutionStage,
    OllamaTransportError,
    OllamaTransportErrorCode,
)


def test_execution_stage_has_exact_values() -> None:
    assert list(OllamaExecutionStage) == [
        OllamaExecutionStage.TRANSPORT,
        OllamaExecutionStage.HTTP_RESPONSE,
        OllamaExecutionStage.OLLAMA_RESPONSE,
        OllamaExecutionStage.EXECUTION_RESULT,
    ]
    assert [
        stage.value
        for stage in OllamaExecutionStage
    ] == [
        "TRANSPORT",
        "HTTP_RESPONSE",
        "OLLAMA_RESPONSE",
        "EXECUTION_RESULT",
    ]


def test_execution_error_code_has_exact_values() -> None:
    assert [
        code.value
        for code in OllamaExecutionErrorCode
    ] == [
        "CONNECT_TIMEOUT",
        "READ_TIMEOUT",
        "WRITE_TIMEOUT",
        "POOL_TIMEOUT",
        "NETWORK_ERROR",
        "PROTOCOL_ERROR",
        "HTTP_STATUS_ERROR",
        "INVALID_JSON_RESPONSE",
        "INVALID_RESPONSE",
        "MODEL_MISMATCH",
        "EMPTY_RESPONSE",
        "GENERATION_INCOMPLETE",
        "INVALID_EXECUTION_RESULT",
    ]


def test_transport_error_code_has_exact_values() -> None:
    assert [
        code.value
        for code in OllamaTransportErrorCode
    ] == [
        "CONNECT_TIMEOUT",
        "READ_TIMEOUT",
        "WRITE_TIMEOUT",
        "POOL_TIMEOUT",
        "NETWORK_ERROR",
        "PROTOCOL_ERROR",
        "HTTP_STATUS_ERROR",
        "INVALID_JSON_RESPONSE",
    ]


def test_execution_error_preserves_exact_attributes() -> None:
    cause = RuntimeError("internal failure")

    error = OllamaExecutionError(
        code=(
            OllamaExecutionErrorCode
            .HTTP_STATUS_ERROR
        ),
        stage=OllamaExecutionStage.HTTP_RESPONSE,
        message="ollama returned a non-success status",
        status_code=503,
        cause=cause,
    )

    assert error.code is (
        OllamaExecutionErrorCode.HTTP_STATUS_ERROR
    )
    assert error.stage is (
        OllamaExecutionStage.HTTP_RESPONSE
    )
    assert error.message == (
        "ollama returned a non-success status"
    )
    assert error.status_code == 503
    assert error.cause is cause
    assert error.args == (
        "ollama returned a non-success status",
    )
    assert str(error) == (
        "HTTP_STATUS_ERROR: "
        "ollama returned a non-success status"
    )


def test_transport_error_preserves_exact_attributes() -> None:
    cause = RuntimeError("internal failure")

    error = OllamaTransportError(
        code=OllamaTransportErrorCode.READ_TIMEOUT,
        message="ollama response timed out",
        cause=cause,
    )

    assert error.code is (
        OllamaTransportErrorCode.READ_TIMEOUT
    )
    assert error.message == (
        "ollama response timed out"
    )
    assert error.status_code is None
    assert error.cause is cause
    assert error.args == (
        "ollama response timed out",
    )
    assert str(error) == (
        "READ_TIMEOUT: ollama response timed out"
    )


def test_error_domains_are_independent() -> None:
    execution_error = OllamaExecutionError(
        code=OllamaExecutionErrorCode.NETWORK_ERROR,
        stage=OllamaExecutionStage.TRANSPORT,
        message="ollama network request failed",
    )
    transport_error = OllamaTransportError(
        code=OllamaTransportErrorCode.NETWORK_ERROR,
        message="ollama network request failed",
    )

    assert not isinstance(
        execution_error,
        OllamaTransportError,
    )
    assert not isinstance(
        transport_error,
        OllamaExecutionError,
    )


@pytest.mark.parametrize(
    ("error_type", "kwargs"),
    [
        (
            OllamaExecutionError,
            {
                "code": (
                    OllamaExecutionErrorCode
                    .NETWORK_ERROR
                ),
                "stage": (
                    OllamaExecutionStage.TRANSPORT
                ),
                "message": (
                    "ollama network request failed"
                ),
            },
        ),
        (
            OllamaTransportError,
            {
                "code": (
                    OllamaTransportErrorCode
                    .NETWORK_ERROR
                ),
                "message": (
                    "ollama network request failed"
                ),
            },
        ),
    ],
)
def test_raise_from_preserves_original_cause(
    error_type: type[
        OllamaExecutionError
        | OllamaTransportError
    ],
    kwargs: dict[str, Any],
) -> None:
    original = RuntimeError("internal failure")

    try:
        raise error_type(
            **kwargs,
            cause=original,
        ) from original
    except error_type as error:
        assert error.cause is original
        assert error.__cause__ is original


@pytest.mark.parametrize(
    "error",
    [
        OllamaExecutionError(
            code=OllamaExecutionErrorCode.NETWORK_ERROR,
            stage=OllamaExecutionStage.TRANSPORT,
            message="ollama network request failed",
            cause=RuntimeError(
                "SENSITIVE_USER_PROMPT"
            ),
        ),
        OllamaTransportError(
            code=OllamaTransportErrorCode.NETWORK_ERROR,
            message="ollama network request failed",
            cause=RuntimeError(
                "SENSITIVE_SYSTEM_PROMPT"
            ),
        ),
    ],
)
def test_error_text_does_not_expose_cause(
    error: (
        OllamaExecutionError
        | OllamaTransportError
    ),
) -> None:
    serialized = (
        str(error)
        + repr(error)
    )

    assert "SENSITIVE_USER_PROMPT" not in serialized
    assert "SENSITIVE_SYSTEM_PROMPT" not in serialized
    assert "RuntimeError" not in serialized
