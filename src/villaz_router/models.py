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

        successful_reasons = {
            RoutingReason.SECURITY_REVIEW_DETECTED,
            RoutingReason.FISCAL_FINANCE_DETECTED,
            RoutingReason.DOCUMENTATION_INTENT_DETECTED,
            RoutingReason.UNITY_DETECTED,
            RoutingReason.MOBILE_DETECTED,
        }

        if self.state is RouteState.EXPLICIT:
            if self.reason is not RoutingReason.USER_SELECTED_PROFILE:
                raise ValueError(
                    "state=explicit requires reason=user_selected_profile"
                )

        if self.state is RouteState.ROUTED:
            if self.reason not in successful_reasons:
                raise ValueError(
                    "state=routed requires a successful routing reason"
                )

        if self.state is RouteState.AMBIGUOUS:
            if self.reason is not RoutingReason.AMBIGUOUS_ROUTE:
                raise ValueError(
                    "state=ambiguous requires reason=ambiguous_route"
                )

        if self.state is RouteState.UNROUTED:
            if self.reason is not RoutingReason.INSUFFICIENT_EVIDENCE:
                raise ValueError(
                    "state=unrouted requires reason=insufficient_evidence"
                )

        if self.state in {RouteState.EXPLICIT, RouteState.ROUTED}:
            if self.candidates:
                raise ValueError(
                    "successful decisions cannot contain candidates"
                )

        if self.conflict_resolved and self.state is not RouteState.ROUTED:
            raise ValueError(
                "conflict_resolved is only valid for routed decisions"
            )

        return self


class EvidenceType(StrEnum):
    TERM = "term"
    PHRASE = "phrase"


class EvidenceStrength(StrEnum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


class Evidence(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str
    type: EvidenceType
    strength: EvidenceStrength
    value: str


class Profile(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str
    enabled: bool


class Domain(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str
    evidence: tuple[Evidence, ...]


class Intent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str
    route_capable: bool
    evidence: tuple[Evidence, ...]


class RouteCondition(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    intent: str | None = None
    domain: str | None = None

    @model_validator(mode="after")
    def validate_condition(self) -> "RouteCondition":
        if self.intent is None and self.domain is None:
            raise ValueError(
                "route condition requires intent, domain, or both"
            )

        return self


class RouteResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    profile: str


class Route(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str
    enabled: bool
    priority: int
    when: RouteCondition
    result: RouteResult


class ProfilesDocument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    schema_version: str
    ruleset_version: str
    profiles: tuple[Profile, ...]


class DomainsDocument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    schema_version: str
    ruleset_version: str
    domains: tuple[Domain, ...]


class IntentsDocument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    schema_version: str
    ruleset_version: str
    intents: tuple[Intent, ...]


class RoutingDocument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    schema_version: str
    ruleset_version: str
    routes: tuple[Route, ...]


class RulesetSnapshot(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    schema_version: str
    ruleset_version: str
    ruleset_hash: str

    profiles: tuple[Profile, ...]
    domains: tuple[Domain, ...]
    intents: tuple[Intent, ...]
    routes: tuple[Route, ...]
