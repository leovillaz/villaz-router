from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RouteState(StrEnum):
    EXPLICIT = "explicit"
    ROUTED = "routed"
    AMBIGUOUS = "ambiguous"
    UNROUTED = "unrouted"


class RoutingMode(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"


class RoutingReason(StrEnum):
    USER_SELECTED_PROFILE = "user_selected_profile"
    SECURITY_REVIEW_DETECTED = "security_review_detected"
    FISCAL_FINANCE_DETECTED = "fiscal_finance_detected"
    DOCUMENTATION_INTENT_DETECTED = "documentation_intent_detected"
    UNITY_DETECTED = "unity_detected"
    MOBILE_DETECTED = "mobile_detected"
    AMBIGUOUS_ROUTE = "ambiguous_route"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RouteRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
    )

    message: str
    explicit_profile: str | None = None


class RouteDecision(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    state: RouteState
    profile: str | None
    mode: RoutingMode
    reason: RoutingReason

    conflict_resolved: bool = False
    candidates: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_state_contract(self) -> "RouteDecision":
        if self.state in {RouteState.EXPLICIT, RouteState.ROUTED}:
            if self.profile is None:
                raise ValueError(
                    f"state={self.state.value} requires a profile"
                )

        if self.state in {RouteState.AMBIGUOUS, RouteState.UNROUTED}:
            if self.profile is not None:
                raise ValueError(
                    f"state={self.state.value} requires profile=None"
                )

        if self.state is RouteState.EXPLICIT:
            if self.mode is not RoutingMode.MANUAL:
                raise ValueError(
                    "state=explicit requires mode=manual"
                )
        else:
            if self.mode is not RoutingMode.AUTO:
                raise ValueError(
                    f"state={self.state.value} requires mode=auto"
                )

        if len(self.candidates) != len(set(self.candidates)):
            raise ValueError("candidates cannot contain duplicates")

        if self.profile is not None and self.profile in self.candidates:
            raise ValueError(
                "selected profile cannot also be listed as a candidate"
            )

        return self
