from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

class LivenessResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    status: Literal["alive"] = "alive"


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    status: Literal["ready", "not_ready"] = "ready"

class PromptMetrics(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )

    output_tokens: StrictInt
    generation_duration_ns: StrictInt
    tokens_per_second: StrictFloat

    @field_validator("output_tokens")
    @classmethod
    def validate_output_tokens(
        cls,
        value: int,
    ) -> int:
        if value < 0:
            raise ValueError(
                "output_tokens must be greater than "
                "or equal to zero"
            )

        return value

    @field_validator("generation_duration_ns")
    @classmethod
    def validate_generation_duration_ns(
        cls,
        value: int,
    ) -> int:
        if value <= 0:
            raise ValueError(
                "generation_duration_ns must be "
                "greater than zero"
            )

        return value

    @field_validator(
        "tokens_per_second",
        mode="before",
    )
    @classmethod
    def validate_tokens_per_second(
        cls,
        value: object,
    ) -> object:
        if type(value) is not float:
            raise ValueError(
                "tokens_per_second must be an exact float"
            )

        if value < 0:
            raise ValueError(
                "tokens_per_second must be greater than "
                "or equal to zero"
            )

        return value

class PromptRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    message: StrictStr = Field(
        min_length=1,
        max_length=16_384,
    )
    explicit_profile: StrictStr | None = Field(
        default=None,
        min_length=1,
        max_length=128,
    )

    @field_validator("message")
    @classmethod
    def validate_message(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "message must not be whitespace-only"
            )
        return value

    @field_validator("explicit_profile")
    @classmethod
    def validate_explicit_profile(
        cls,
        value: str | None,
    ) -> str | None:
        if (
            value is not None
            and value.strip() == ""
        ):
            raise ValueError(
                "explicit_profile must not be "
                "whitespace-only"
            )
        return value


class PromptResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    response: StrictStr
    profile: StrictStr
    model: StrictStr
    state: Literal["explicit", "routed"]
    route_id: StrictStr | None
    metrics: PromptMetrics

    @field_validator(
        "response",
        "profile",
        "model",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "value must not be empty or whitespace-only"
            )
        return value

    @field_validator("route_id")
    @classmethod
    def validate_route_id(
        cls,
        value: str | None,
    ) -> str | None:
        if (
            value is not None
            and value.strip() == ""
        ):
            raise ValueError(
                "route_id must not be empty or whitespace-only"
            )
        return value

    @model_validator(mode="after")
    def validate_state_coherence(
        self,
    ) -> "PromptResponse":
        if self.state == "routed":
            if self.route_id is None:
                raise ValueError(
                    "state=routed requires route_id"
                )
            return self

        if self.route_id is not None:
            raise ValueError(
                "state=explicit requires route_id=None"
            )

        return self

class AmbiguousCandidate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    route_id: StrictStr
    profile: StrictStr
    comparison_score: int = Field(ge=0)

    @field_validator(
        "route_id",
        "profile",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "value must not be empty or whitespace-only"
            )
        return value


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    code: StrictStr
    message: StrictStr
    candidates: tuple[AmbiguousCandidate, ...] | None = None

    @field_validator(
        "code",
        "message",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "value must not be empty or whitespace-only"
            )
        return value

    @model_validator(mode="after")
    def validate_candidates_coherence(
        self,
    ) -> "ErrorEnvelope":
        if self.code == "AMBIGUOUS_ROUTE":
            if (
                self.candidates is None
                or len(self.candidates) < 2
            ):
                raise ValueError(
                    "AMBIGUOUS_ROUTE requires "
                    "at least two candidates"
                )
            return self

        if self.candidates is not None:
            raise ValueError(
                "candidates are only valid for "
                "AMBIGUOUS_ROUTE"
            )

        return self
class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )

    error: ErrorEnvelope
