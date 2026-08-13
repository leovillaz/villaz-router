from enum import StrEnum


class RouterErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_PROFILE = "UNKNOWN_PROFILE"
    PROFILE_DISABLED = "PROFILE_DISABLED"
    INVALID_RULESET = "INVALID_RULESET"


class RouterError(Exception):
    def __init__(
        self,
        code: RouterErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
