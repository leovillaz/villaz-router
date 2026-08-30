from enum import StrEnum


class OllamaExecutionStage(StrEnum):
    TRANSPORT = "TRANSPORT"
    HTTP_RESPONSE = "HTTP_RESPONSE"
    OLLAMA_RESPONSE = "OLLAMA_RESPONSE"
    EXECUTION_RESULT = "EXECUTION_RESULT"


class OllamaExecutionErrorCode(StrEnum):
    CONNECT_TIMEOUT = "CONNECT_TIMEOUT"
    READ_TIMEOUT = "READ_TIMEOUT"
    WRITE_TIMEOUT = "WRITE_TIMEOUT"
    POOL_TIMEOUT = "POOL_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    HTTP_STATUS_ERROR = "HTTP_STATUS_ERROR"
    INVALID_JSON_RESPONSE = "INVALID_JSON_RESPONSE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    MODEL_MISMATCH = "MODEL_MISMATCH"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    GENERATION_INCOMPLETE = "GENERATION_INCOMPLETE"
    INVALID_EXECUTION_RESULT = "INVALID_EXECUTION_RESULT"


class OllamaTransportErrorCode(StrEnum):
    CONNECT_TIMEOUT = "CONNECT_TIMEOUT"
    READ_TIMEOUT = "READ_TIMEOUT"
    WRITE_TIMEOUT = "WRITE_TIMEOUT"
    POOL_TIMEOUT = "POOL_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    HTTP_STATUS_ERROR = "HTTP_STATUS_ERROR"
    INVALID_JSON_RESPONSE = "INVALID_JSON_RESPONSE"


class OllamaExecutionError(Exception):
    def __init__(
        self,
        code: OllamaExecutionErrorCode,
        stage: OllamaExecutionStage,
        message: str,
        status_code: int | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.status_code = status_code
        self.cause = cause

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


class OllamaTransportError(Exception):
    def __init__(
        self,
        code: OllamaTransportErrorCode,
        message: str,
        status_code: int | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.cause = cause

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
