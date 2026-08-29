from typing import Literal

from pydantic import BaseModel, ConfigDict


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

    status: Literal["ready"] = "ready"
