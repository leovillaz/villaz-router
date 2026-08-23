from enum import StrEnum


class RegistryErrorCode(StrEnum):
    INVALID_PROFILE_DEFINITION = "INVALID_PROFILE_DEFINITION"
    DUPLICATE_PROFILE_ID = "DUPLICATE_PROFILE_ID"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    INVALID_REGISTRY = "INVALID_REGISTRY"


class RegistryError(Exception):
    def __init__(
        self,
        code: RegistryErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
