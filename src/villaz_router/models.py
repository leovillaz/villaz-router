from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from villaz_router.config import RouterSettings


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


class RouteCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    route_id: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    comparison_score: int = Field(ge=0)


class RouteDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: RouteState
    profile: str | None
    route_id: str | None = None
    comparison_score: int | None = Field(default=None, ge=0)
    mode: RoutingMode
    reason: RoutingReason
    conflict_resolved: bool = False
    candidates: tuple[RouteCandidate, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_state_contract(self) -> "RouteDecision":
        successful_reasons = {
            RoutingReason.SECURITY_REVIEW_DETECTED,
            RoutingReason.FISCAL_FINANCE_DETECTED,
            RoutingReason.DOCUMENTATION_INTENT_DETECTED,
            RoutingReason.UNITY_DETECTED,
            RoutingReason.MOBILE_DETECTED,
        }

        if self.state is RouteState.EXPLICIT:
            if self.profile is None:
                raise ValueError("state=explicit requires a profile")
            if self.route_id is not None:
                raise ValueError("state=explicit requires route_id=None")
            if self.comparison_score is not None:
                raise ValueError("state=explicit requires comparison_score=None")
            if self.mode is not RoutingMode.MANUAL:
                raise ValueError("state=explicit requires mode=manual")
            if self.reason is not RoutingReason.USER_SELECTED_PROFILE:
                raise ValueError("state=explicit requires reason=user_selected_profile")
            if self.conflict_resolved:
                raise ValueError("state=explicit requires conflict_resolved=False")
            if self.candidates:
                raise ValueError("state=explicit requires candidates=()")

        elif self.state is RouteState.ROUTED:
            if self.profile is None:
                raise ValueError("state=routed requires a profile")
            if self.route_id is None:
                raise ValueError("state=routed requires a route_id")
            if self.comparison_score is None:
                raise ValueError("state=routed requires a comparison_score")
            if self.mode is not RoutingMode.AUTO:
                raise ValueError("state=routed requires mode=auto")
            if self.reason not in successful_reasons:
                raise ValueError("state=routed requires a successful routing reason")
            if self.candidates:
                raise ValueError("state=routed requires candidates=()")

        elif self.state is RouteState.AMBIGUOUS:
            if self.profile is not None:
                raise ValueError("state=ambiguous requires profile=None")
            if self.route_id is not None:
                raise ValueError("state=ambiguous requires route_id=None")
            if self.comparison_score is not None:
                raise ValueError("state=ambiguous requires comparison_score=None")
            if self.mode is not RoutingMode.AUTO:
                raise ValueError("state=ambiguous requires mode=auto")
            if self.reason is not RoutingReason.AMBIGUOUS_ROUTE:
                raise ValueError("state=ambiguous requires reason=ambiguous_route")
            if self.conflict_resolved:
                raise ValueError("state=ambiguous requires conflict_resolved=False")
            if len(self.candidates) < 2:
                raise ValueError("state=ambiguous requires at least two candidates")

            route_ids = tuple(candidate.route_id for candidate in self.candidates)
            if len(route_ids) != len(set(route_ids)):
                raise ValueError("ambiguous candidates require distinct route_id values")

            canonical_candidates = tuple(
                sorted(
                    self.candidates,
                    key=lambda candidate: (
                        -candidate.comparison_score,
                        candidate.route_id,
                    ),
                )
            )
            if self.candidates != canonical_candidates:
                raise ValueError(
                    "ambiguous candidates must be ordered by comparison_score DESC then route_id ASC"
                )

        elif self.state is RouteState.UNROUTED:
            if self.profile is not None:
                raise ValueError("state=unrouted requires profile=None")
            if self.route_id is not None:
                raise ValueError("state=unrouted requires route_id=None")
            if self.comparison_score is not None:
                raise ValueError("state=unrouted requires comparison_score=None")
            if self.mode is not RoutingMode.AUTO:
                raise ValueError("state=unrouted requires mode=auto")
            if self.reason is not RoutingReason.INSUFFICIENT_EVIDENCE:
                raise ValueError("state=unrouted requires reason=insufficient_evidence")
            if self.conflict_resolved:
                raise ValueError("state=unrouted requires conflict_resolved=False")
            if self.candidates:
                raise ValueError("state=unrouted requires candidates=()")

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



class EvidenceMatch(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    evidence_id: str = Field(min_length=1)
    evidence_type: EvidenceType
    evidence_value: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int

    @model_validator(mode="after")
    def validate_span(self) -> "EvidenceMatch":
        if self.end <= self.start:
            raise ValueError("end must be greater than start")

        return self


class EvidenceContribution(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    evidence_id: str = Field(min_length=1)
    strength: EvidenceStrength
    weight: int = Field(gt=0)


class ScoringResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    score: int = Field(ge=0)
    contributions: tuple[EvidenceContribution, ...] = Field(
        default_factory=tuple
    )

    @model_validator(mode="after")
    def validate_score_total(self) -> "ScoringResult":
        expected_score = sum(
            contribution.weight
            for contribution in self.contributions
        )
        if self.score != expected_score:
            raise ValueError(
                "score must equal the sum of contribution weights"
            )

        return self


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
    ruleset_hash: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    router: RouterSettings
    profiles: tuple[Profile, ...]
    domains: tuple[Domain, ...]
    intents: tuple[Intent, ...]
    routes: tuple[Route, ...]
