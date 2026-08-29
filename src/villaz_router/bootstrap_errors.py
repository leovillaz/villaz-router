from enum import StrEnum


class BootstrapStage(StrEnum):
    CONFIGURATION_ROOT = "CONFIGURATION_ROOT"
    RULESET = "RULESET"
    PROFILE_REGISTRY = "PROFILE_REGISTRY"
    RUNTIME_COMPATIBILITY = "RUNTIME_COMPATIBILITY"
    RUNTIME_CONTEXT = "RUNTIME_CONTEXT"


class ApplicationBootstrapErrorCode(StrEnum):
    ROOT_REQUIRED = "ROOT_REQUIRED"
    ROOT_NOT_FOUND = "ROOT_NOT_FOUND"
    ROOT_NOT_DIRECTORY = "ROOT_NOT_DIRECTORY"
    ROOT_NOT_READABLE = "ROOT_NOT_READABLE"
    RULESET_LOAD_FAILED = "RULESET_LOAD_FAILED"
    PROFILE_REGISTRY_LOAD_FAILED = "PROFILE_REGISTRY_LOAD_FAILED"
    RUNTIME_COMPATIBILITY_FAILED = "RUNTIME_COMPATIBILITY_FAILED"
    RUNTIME_CONTEXT_CREATION_FAILED = "RUNTIME_CONTEXT_CREATION_FAILED"


class ApplicationBootstrapError(Exception):
    def __init__(
        self,
        code: ApplicationBootstrapErrorCode,
        stage: BootstrapStage,
        message: str,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
