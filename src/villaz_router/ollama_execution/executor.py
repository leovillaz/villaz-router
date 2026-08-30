from collections.abc import Mapping
from types import TracebackType
from typing import NoReturn

from pydantic import ValidationError

from villaz_router.ollama_execution.errors import (
    OllamaExecutionError,
    OllamaExecutionErrorCode,
    OllamaExecutionStage,
    OllamaTransportError,
    OllamaTransportErrorCode,
)
from villaz_router.ollama_execution.models import (
    OllamaExecutionRequest,
    OllamaExecutionResult,
)
from villaz_router.ollama_execution.transport import (
    OllamaTransport,
)


_TRANSPORT_ERROR_MAPPING: dict[
    OllamaTransportErrorCode,
    tuple[
        OllamaExecutionErrorCode,
        OllamaExecutionStage,
        str,
    ],
] = {
    OllamaTransportErrorCode.CONNECT_TIMEOUT: (
        OllamaExecutionErrorCode.CONNECT_TIMEOUT,
        OllamaExecutionStage.TRANSPORT,
        "unable to connect to ollama before timeout",
    ),
    OllamaTransportErrorCode.READ_TIMEOUT: (
        OllamaExecutionErrorCode.READ_TIMEOUT,
        OllamaExecutionStage.TRANSPORT,
        "ollama response timed out",
    ),
    OllamaTransportErrorCode.WRITE_TIMEOUT: (
        OllamaExecutionErrorCode.WRITE_TIMEOUT,
        OllamaExecutionStage.TRANSPORT,
        "ollama request write timed out",
    ),
    OllamaTransportErrorCode.POOL_TIMEOUT: (
        OllamaExecutionErrorCode.POOL_TIMEOUT,
        OllamaExecutionStage.TRANSPORT,
        "ollama connection pool timed out",
    ),
    OllamaTransportErrorCode.NETWORK_ERROR: (
        OllamaExecutionErrorCode.NETWORK_ERROR,
        OllamaExecutionStage.TRANSPORT,
        "ollama network request failed",
    ),
    OllamaTransportErrorCode.PROTOCOL_ERROR: (
        OllamaExecutionErrorCode.PROTOCOL_ERROR,
        OllamaExecutionStage.TRANSPORT,
        "ollama protocol failure",
    ),
    OllamaTransportErrorCode.HTTP_STATUS_ERROR: (
        OllamaExecutionErrorCode.HTTP_STATUS_ERROR,
        OllamaExecutionStage.HTTP_RESPONSE,
        "ollama returned a non-success status",
    ),
    OllamaTransportErrorCode.INVALID_JSON_RESPONSE: (
        OllamaExecutionErrorCode.INVALID_JSON_RESPONSE,
        OllamaExecutionStage.HTTP_RESPONSE,
        "ollama returned invalid JSON",
    ),
}


def _raise_transport_error(
    error: OllamaTransportError,
) -> NoReturn:
    code, stage, message = _TRANSPORT_ERROR_MAPPING[
        error.code
    ]

    raise OllamaExecutionError(
        code=code,
        stage=stage,
        message=message,
        status_code=error.status_code,
        cause=error,
    ) from error


def _raise_invalid_response(
    code: OllamaExecutionErrorCode,
    message: str,
) -> NoReturn:
    raise OllamaExecutionError(
        code=code,
        stage=OllamaExecutionStage.OLLAMA_RESPONSE,
        message=message,
    )


class OllamaExecutor:
    def __init__(
        self,
        transport: OllamaTransport,
    ) -> None:
        self._transport = transport
        self._closed = False

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(
                "ollama executor is closed"
            )

    async def execute(
        self,
        request: OllamaExecutionRequest,
    ) -> OllamaExecutionResult:
        self._ensure_open()

        dispatch_plan = request.dispatch_plan

        payload: dict[str, object] = {
            "model": dispatch_plan.model,
            "system": dispatch_plan.system_prompt,
            "prompt": request.user_prompt,
            "stream": False,
            "raw": False,
            "think": False,
        }

        try:
            response = await self._transport.generate(
                payload
            )
        except OllamaTransportError as exc:
            _raise_transport_error(exc)

        if not isinstance(response, Mapping):
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .INVALID_RESPONSE,
                "ollama response must be an object",
            )

        response_model = response.get("model")

        if (
            not isinstance(response_model, str)
            or response_model.strip() == ""
        ):
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .INVALID_RESPONSE,
                "ollama response contains an invalid model",
            )

        if response_model != dispatch_plan.model:
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .MODEL_MISMATCH,
                "ollama response model does not match "
                "the dispatch plan",
            )

        response_text = response.get("response")

        if not isinstance(response_text, str):
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .INVALID_RESPONSE,
                "ollama response contains invalid text",
            )

        if response_text.strip() == "":
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .EMPTY_RESPONSE,
                "ollama returned an empty response",
            )

        done = response.get("done")

        if type(done) is not bool:
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .INVALID_RESPONSE,
                "ollama response contains an invalid "
                "completion state",
            )

        if done is not True:
            _raise_invalid_response(
                OllamaExecutionErrorCode
                .GENERATION_INCOMPLETE,
                "ollama generation did not complete",
            )

        try:
            return OllamaExecutionResult(
                model=response_model,
                response_text=response_text,
            )
        except ValidationError as exc:
            raise OllamaExecutionError(
                code=(
                    OllamaExecutionErrorCode
                    .INVALID_EXECUTION_RESULT
                ),
                stage=(
                    OllamaExecutionStage
                    .EXECUTION_RESULT
                ),
                message=(
                    "unable to construct ollama "
                    "execution result"
                ),
                cause=exc,
            ) from exc

    async def aclose(self) -> None:
        if self._closed:
            return

        self._closed = True
        await self._transport.aclose()

    async def __aenter__(
        self,
    ) -> "OllamaExecutor":
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
