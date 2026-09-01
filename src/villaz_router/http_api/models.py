from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
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
