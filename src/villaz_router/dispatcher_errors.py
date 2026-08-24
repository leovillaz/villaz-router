from enum import StrEnum


class DispatcherErrorCode(StrEnum):
    INVALID_ROUTE_DECISION = "INVALID_ROUTE_DECISION"
    NON_DISPATCHABLE_DECISION = "NON_DISPATCHABLE_DECISION"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_DISABLED = "PROFILE_DISABLED"
    INVALID_DISPATCH_PLAN = "INVALID_DISPATCH_PLAN"


class DispatcherError(Exception):
    def __init__(self, code: DispatcherErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
