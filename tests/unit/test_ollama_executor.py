import inspect
from typing import Any

import anyio
import pytest
from pydantic import ValidationError

import villaz_router.ollama_execution.executor as executor_module
from villaz_router.dispatcher_models import DispatchPlan
from villaz_router.models import RouteState
from villaz_router.ollama_execution.errors import (
    OllamaExecutionError,
    OllamaExecutionErrorCode,
    OllamaExecutionStage,
    OllamaTransportError,
    OllamaTransportErrorCode,
)
from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)
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


def make_request() -> OllamaExecutionRequest:
    return OllamaExecutionRequest(
        dispatch_plan=make_dispatch_plan(),
        user_prompt="Explain the architecture.",
    )


def make_valid_response() -> dict[str, object]:
    return {
        "model": "gemma3:12b",
        "response": "Generated response.",
        "done": True,
    }

_USE_VALID_RESPONSE = object()


class FakeTransport:
    def __init__(
        self,
        response: object = _USE_VALID_RESPONSE,
        error: BaseException | None = None,
    ) -> None:
        self.response = (
            make_valid_response()
            if response is _USE_VALID_RESPONSE
            else response
        )
        self.error = error
        self.payloads: list[
            dict[str, object]
        ] = []
        self.close_calls = 0

    async def generate(
        self,
        payload: dict[str, object],
    ) -> object:
        self.payloads.append(payload)

        if self.error is not None:
            raise self.error

        return self.response

    async def aclose(self) -> None:
        self.close_calls += 1


def test_executor_has_exact_async_operations() -> None:
    execute_signature = inspect.signature(
        OllamaExecutor.execute
    )
    close_signature = inspect.signature(
        OllamaExecutor.aclose
    )

    assert tuple(
        execute_signature.parameters
    ) == (
        "self",
        "request",
    )
    assert (
        execute_signature.parameters[
            "request"
        ].annotation
        is OllamaExecutionRequest
    )
    assert (
        execute_signature.return_annotation
        is OllamaExecutionResult
    )
    assert inspect.iscoroutinefunction(
        OllamaExecutor.execute
    )

    assert tuple(
        close_signature.parameters
    ) == ("self",)
    assert close_signature.return_annotation is None
    assert inspect.iscoroutinefunction(
        OllamaExecutor.aclose
    )


def test_executor_construction_performs_no_transport_io() -> None:
    transport = FakeTransport()

    executor = OllamaExecutor(transport)

    assert isinstance(executor, OllamaExecutor)
    assert transport.payloads == []
    assert transport.close_calls == 0


@pytest.mark.anyio
async def test_execute_sends_exact_payload() -> None:
    transport = FakeTransport()
    executor = OllamaExecutor(transport)
    request = make_request()

    result = await executor.execute(request)

    assert transport.payloads == [{
        "model": "gemma3:12b",
        "system": "Canonical system prompt.",
        "prompt": "Explain the architecture.",
        "stream": False,
        "raw": False,
        "think": False,
    }]
    assert result == OllamaExecutionResult(
        model="gemma3:12b",
        response_text="Generated response.",
    )


@pytest.mark.anyio
async def test_execute_preserves_exact_sensitive_text() -> None:
    dispatch_plan = DispatchPlan(
        profile_id="docs-dev",
        model="gemma3:12b",
        system_prompt=(
            "  SENSITIVE_SYSTEM_PROMPT\n"
        ),
        registry_hash="b" * 64,
        source_state=RouteState.EXPLICIT,
        route_id=None,
    )
    request = OllamaExecutionRequest(
        dispatch_plan=dispatch_plan,
        user_prompt="  SENSITIVE_USER_PROMPT\n",
    )
    response_text = (
        "  SENSITIVE_MODEL_RESPONSE\n"
    )
    transport = FakeTransport({
        "model": "gemma3:12b",
        "response": response_text,
        "done": True,
        "ignored_metadata": {
            "duration": 123,
        },
    })
    executor = OllamaExecutor(transport)

    result = await executor.execute(request)

    assert transport.payloads[0]["system"] == (
        "  SENSITIVE_SYSTEM_PROMPT\n"
    )
    assert transport.payloads[0]["prompt"] == (
        "  SENSITIVE_USER_PROMPT\n"
    )
    assert result.response_text == response_text


@pytest.mark.parametrize(
    (
        "transport_code",
        "execution_code",
        "stage",
        "message",
        "status_code",
    ),
    [
        (
            OllamaTransportErrorCode
            .CONNECT_TIMEOUT,
            OllamaExecutionErrorCode
            .CONNECT_TIMEOUT,
            OllamaExecutionStage.TRANSPORT,
            (
                "unable to connect to ollama "
                "before timeout"
            ),
            None,
        ),
        (
            OllamaTransportErrorCode
            .READ_TIMEOUT,
            OllamaExecutionErrorCode.READ_TIMEOUT,
            OllamaExecutionStage.TRANSPORT,
            "ollama response timed out",
            None,
        ),
        (
            OllamaTransportErrorCode
            .WRITE_TIMEOUT,
            OllamaExecutionErrorCode
            .WRITE_TIMEOUT,
            OllamaExecutionStage.TRANSPORT,
            "ollama request write timed out",
            None,
        ),
        (
            OllamaTransportErrorCode
            .POOL_TIMEOUT,
            OllamaExecutionErrorCode.POOL_TIMEOUT,
            OllamaExecutionStage.TRANSPORT,
            "ollama connection pool timed out",
            None,
        ),
        (
            OllamaTransportErrorCode
            .NETWORK_ERROR,
            OllamaExecutionErrorCode.NETWORK_ERROR,
            OllamaExecutionStage.TRANSPORT,
            "ollama network request failed",
            None,
        ),
        (
            OllamaTransportErrorCode
            .PROTOCOL_ERROR,
            OllamaExecutionErrorCode
            .PROTOCOL_ERROR,
            OllamaExecutionStage.TRANSPORT,
            "ollama protocol failure",
            None,
        ),
        (
            OllamaTransportErrorCode
            .HTTP_STATUS_ERROR,
            OllamaExecutionErrorCode
            .HTTP_STATUS_ERROR,
            OllamaExecutionStage.HTTP_RESPONSE,
            (
                "ollama returned a "
                "non-success status"
            ),
            503,
        ),
        (
            OllamaTransportErrorCode
            .INVALID_JSON_RESPONSE,
            OllamaExecutionErrorCode
            .INVALID_JSON_RESPONSE,
            OllamaExecutionStage.HTTP_RESPONSE,
            "ollama returned invalid JSON",
            200,
        ),
    ],
)
@pytest.mark.anyio
async def test_execute_translates_transport_errors(
    transport_code: OllamaTransportErrorCode,
    execution_code: OllamaExecutionErrorCode,
    stage: OllamaExecutionStage,
    message: str,
    status_code: int | None,
) -> None:
    internal_cause = RuntimeError(
        "SENSITIVE_INTERNAL_FAILURE"
    )
    transport_error = OllamaTransportError(
        code=transport_code,
        message="technical transport failure",
        status_code=status_code,
        cause=internal_cause,
    )
    transport = FakeTransport(
        error=transport_error
    )
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    error = exc_info.value

    assert error.code is execution_code
    assert error.stage is stage
    assert error.message == message
    assert error.status_code == status_code
    assert error.cause is transport_error
    assert error.__cause__ is transport_error
    assert transport.payloads == [{
        "model": "gemma3:12b",
        "system": "Canonical system prompt.",
        "prompt": "Explain the architecture.",
        "stream": False,
        "raw": False,
        "think": False,
    }]

    serialized = str(error) + repr(error)

    assert (
        "SENSITIVE_INTERNAL_FAILURE"
        not in serialized
    )
    assert (
        "technical transport failure"
        not in serialized
    )


@pytest.mark.anyio
async def test_execute_does_not_retry_transport_failure() -> None:
    transport_error = OllamaTransportError(
        code=(
            OllamaTransportErrorCode
            .NETWORK_ERROR
        ),
        message="technical transport failure",
    )
    transport = FakeTransport(
        error=transport_error
    )
    executor = OllamaExecutor(transport)

    with pytest.raises(OllamaExecutionError):
        await executor.execute(make_request())

    assert len(transport.payloads) == 1


@pytest.mark.anyio
async def test_unexpected_transport_error_is_not_masked() -> None:
    unexpected = RuntimeError(
        "unexpected transport failure"
    )
    transport = FakeTransport(error=unexpected)
    executor = OllamaExecutor(transport)

    with pytest.raises(RuntimeError) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value is unexpected
    assert len(transport.payloads) == 1


@pytest.mark.parametrize(
    "invalid_response",
    [
        None,
        [],
        "invalid",
        1,
        True,
    ],
)
@pytest.mark.anyio
async def test_execute_requires_mapping_response(
    invalid_response: object,
) -> None:
    transport = FakeTransport(invalid_response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    error = exc_info.value

    assert error.code is (
        OllamaExecutionErrorCode.INVALID_RESPONSE
    )
    assert error.stage is (
        OllamaExecutionStage.OLLAMA_RESPONSE
    )
    assert error.cause is None
    assert error.__cause__ is None


@pytest.mark.parametrize(
    "invalid_model",
    [
        None,
        1,
        True,
        "",
        " ",
        "\t\n",
    ],
)
@pytest.mark.anyio
async def test_execute_requires_valid_response_model(
    invalid_model: Any,
) -> None:
    response = make_valid_response()
    response["model"] = invalid_model
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value.code is (
        OllamaExecutionErrorCode.INVALID_RESPONSE
    )


@pytest.mark.anyio
async def test_execute_requires_response_model_field() -> None:
    response = make_valid_response()
    del response["model"]
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value.code is (
        OllamaExecutionErrorCode.INVALID_RESPONSE
    )


@pytest.mark.anyio
async def test_execute_rejects_model_mismatch_first() -> None:
    transport = FakeTransport({
        "model": "different-model:latest",
        "done": False,
    })
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    error = exc_info.value

    assert error.code is (
        OllamaExecutionErrorCode.MODEL_MISMATCH
    )
    assert error.stage is (
        OllamaExecutionStage.OLLAMA_RESPONSE
    )
    assert error.message == (
        "ollama response model does not match "
        "the dispatch plan"
    )


@pytest.mark.parametrize(
    "invalid_text",
    [
        None,
        1,
        True,
        [],
        {},
    ],
)
@pytest.mark.anyio
async def test_execute_requires_string_response_text(
    invalid_text: Any,
) -> None:
    response = make_valid_response()
    response["response"] = invalid_text
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value.code is (
        OllamaExecutionErrorCode.INVALID_RESPONSE
    )


@pytest.mark.parametrize(
    "empty_text",
    [
        "",
        " ",
        "\t",
        "\n",
        " \t\n ",
    ],
)
@pytest.mark.anyio
async def test_execute_rejects_empty_response_text(
    empty_text: str,
) -> None:
    response = make_valid_response()
    response["response"] = empty_text
    response["done"] = False
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value.code is (
        OllamaExecutionErrorCode.EMPTY_RESPONSE
    )


@pytest.mark.parametrize(
    "invalid_done",
    [
        None,
        0,
        1,
        "true",
        [],
        {},
    ],
)
@pytest.mark.anyio
async def test_execute_requires_exact_boolean_done(
    invalid_done: Any,
) -> None:
    response = make_valid_response()
    response["done"] = invalid_done
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value.code is (
        OllamaExecutionErrorCode.INVALID_RESPONSE
    )


@pytest.mark.anyio
async def test_execute_requires_done_field() -> None:
    response = make_valid_response()
    del response["done"]
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    assert exc_info.value.code is (
        OllamaExecutionErrorCode.INVALID_RESPONSE
    )


@pytest.mark.anyio
async def test_execute_rejects_incomplete_generation() -> None:
    response = make_valid_response()
    response["done"] = False
    transport = FakeTransport(response)
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    error = exc_info.value

    assert error.code is (
        OllamaExecutionErrorCode
        .GENERATION_INCOMPLETE
    )
    assert error.stage is (
        OllamaExecutionStage.OLLAMA_RESPONSE
    )


@pytest.mark.anyio
async def test_result_validation_failure_is_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_error = (
        ValidationError.from_exception_data(
            "OllamaExecutionResult",
            [],
        )
    )

    def fail_result_creation(
        **values: object,
    ) -> OllamaExecutionResult:
        raise expected_error

    monkeypatch.setattr(
        executor_module,
        "OllamaExecutionResult",
        fail_result_creation,
    )

    transport = FakeTransport()
    executor = OllamaExecutor(transport)

    with pytest.raises(
        OllamaExecutionError
    ) as exc_info:
        await executor.execute(make_request())

    error = exc_info.value

    assert error.code is (
        OllamaExecutionErrorCode
        .INVALID_EXECUTION_RESULT
    )
    assert error.stage is (
        OllamaExecutionStage.EXECUTION_RESULT
    )
    assert error.cause is expected_error
    assert error.__cause__ is expected_error

@pytest.mark.anyio
async def test_aclose_is_idempotent() -> None:
    transport = FakeTransport()
    executor = OllamaExecutor(transport)

    first_result = await executor.aclose()
    second_result = await executor.aclose()

    assert first_result is None
    assert second_result is None
    assert transport.close_calls == 1


@pytest.mark.anyio
async def test_execute_after_close_is_rejected() -> None:
    transport = FakeTransport()
    executor = OllamaExecutor(transport)
    await executor.aclose()

    with pytest.raises(
        RuntimeError,
        match="^ollama executor is closed$",
    ):
        await executor.execute(make_request())

    assert transport.payloads == []
    assert transport.close_calls == 1


@pytest.mark.anyio
async def test_async_context_manager_owns_transport() -> None:
    transport = FakeTransport()
    executor = OllamaExecutor(transport)

    async with executor as entered:
        assert entered is executor
        assert transport.close_calls == 0

        result = await executor.execute(
            make_request()
        )

        assert isinstance(
            result,
            OllamaExecutionResult,
        )

    assert transport.close_calls == 1


@pytest.mark.anyio
async def test_context_manager_does_not_suppress_error() -> None:
    transport = FakeTransport()
    executor = OllamaExecutor(transport)
    expected = RuntimeError("body failed")

    with pytest.raises(RuntimeError) as exc_info:
        async with executor:
            raise expected

    assert exc_info.value is expected
    assert transport.close_calls == 1


@pytest.mark.anyio
async def test_close_failure_is_not_retried() -> None:
    expected = RuntimeError("close failed")

    class FailingCloseTransport(FakeTransport):
        async def aclose(self) -> None:
            self.close_calls += 1
            raise expected

    transport = FailingCloseTransport()
    executor = OllamaExecutor(transport)

    with pytest.raises(RuntimeError) as exc_info:
        await executor.aclose()

    assert exc_info.value is expected

    second_result = await executor.aclose()

    assert second_result is None
    assert transport.close_calls == 1


@pytest.mark.anyio
async def test_cancellation_is_not_translated() -> None:
    started = anyio.Event()
    finished = anyio.Event()
    wrapped_errors: list[
        OllamaExecutionError
    ] = []

    class BlockingTransport(FakeTransport):
        async def generate(
            self,
            payload: dict[str, object],
        ) -> object:
            self.payloads.append(payload)
            started.set()

            try:
                await anyio.Event().wait()
            finally:
                finished.set()

    transport = BlockingTransport()
    executor = OllamaExecutor(transport)

    async def execute_request() -> None:
        try:
            await executor.execute(make_request())
        except OllamaExecutionError as exc:
            wrapped_errors.append(exc)

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(execute_request)
        await started.wait()
        tasks.cancel_scope.cancel()

    assert finished.is_set()
    assert wrapped_errors == []
    assert len(transport.payloads) == 1
