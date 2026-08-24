from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator

from .models import RouteState


RegistryHash = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


class DispatchPlan(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
    )

    profile_id: StrictStr
    model: StrictStr
    system_prompt: StrictStr
    registry_hash: RegistryHash
    source_state: RouteState
    route_id: StrictStr | None

    @field_validator("profile_id", "model", "system_prompt")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("value must not be empty or whitespace-only")
        return value

    @field_validator("route_id")
    @classmethod
    def validate_route_id(cls, value: str | None) -> str | None:
        if value is not None and value.strip() == "":
            raise ValueError("route_id must not be empty or whitespace-only")
        return value

    @model_validator(mode="after")
    def validate_state_coherence(self) -> "DispatchPlan":
        if self.source_state is RouteState.ROUTED:
            if self.route_id is None:
                raise ValueError("routed dispatch plan requires route_id")
            return self

        if self.source_state is RouteState.EXPLICIT:
            if self.route_id is not None:
                raise ValueError("explicit dispatch plan requires route_id to be None")
            return self

        raise ValueError("source_state must be routed or explicit")
