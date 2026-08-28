from enum import StrEnum


class RuntimeCompatibilityErrorCode(StrEnum):
    INCOMPATIBLE_RUNTIME_CONFIGURATION = "INCOMPATIBLE_RUNTIME_CONFIGURATION"


class RuntimeCompatibilityReason(StrEnum):
    PROFILE_MISSING_FROM_REGISTRY = "PROFILE_MISSING_FROM_REGISTRY"
    PROFILE_EXTRA_IN_REGISTRY = "PROFILE_EXTRA_IN_REGISTRY"
    ROUTE_REFERENCES_UNKNOWN_PROFILE = "ROUTE_REFERENCES_UNKNOWN_PROFILE"
    PROFILE_ENABLED_MISMATCH = "PROFILE_ENABLED_MISMATCH"


class RuntimeCompatibilityError(Exception):
    def __init__(
        self,
        code: RuntimeCompatibilityErrorCode,
        reason: RuntimeCompatibilityReason,
        profile_id: str,
        route_id: str | None,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.reason = reason
        self.profile_id = profile_id
        self.route_id = route_id
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
