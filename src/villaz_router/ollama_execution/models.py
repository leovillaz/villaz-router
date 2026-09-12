from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
    StrictStr,
    field_validator,
)

from villaz_router.dispatcher_models import DispatchPlan


class OllamaExecutionTurn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    user: StrictStr
    assistant: StrictStr

    @field_validator(
        "user",
        "assistant",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "value must not be empty "
                "or whitespace-only"
            )

        return value


class OllamaExecutionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    dispatch_plan: DispatchPlan
    history: tuple[OllamaExecutionTurn, ...] = ()
    user_prompt: StrictStr

    @field_validator(
        "dispatch_plan",
        mode="before",
    )
    @classmethod
    def validate_dispatch_plan_type(
        cls,
        value: object,
    ) -> object:
        if not isinstance(value, DispatchPlan):
            raise ValueError(
                "dispatch_plan must be a "
                "DispatchPlan instance"
            )

        return value

    @field_validator(
        "history",
        mode="before",
    )
    @classmethod
    def validate_history_type(
        cls,
        value: object,
    ) -> object:
        if type(value) is not tuple:
            raise ValueError(
                "history must be a tuple"
            )

        if not all(
            isinstance(
                turn,
                OllamaExecutionTurn,
            )
            for turn in value
        ):
            raise ValueError(
                "history must contain only "
                "OllamaExecutionTurn instances"
            )

        return value

    @field_validator("user_prompt")
    @classmethod
    def validate_user_prompt(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "user_prompt must not be empty "
                "or whitespace-only"
            )

        return value


class OllamaExecutionResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    model: StrictStr
    response_text: StrictStr
    output_tokens: StrictInt
    generation_duration_ns: StrictInt

    @field_validator(
        "model",
        "response_text",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "value must not be empty "
                "or whitespace-only"
            )

        return value

    @field_validator(
        "output_tokens",
        "generation_duration_ns",
    )
    @classmethod
    def validate_generation_metrics(
        cls,
        value: int,
        info,
    ) -> int:
        if info.field_name == "output_tokens":
            if value < 0:
                raise ValueError(
                    "output_tokens must be greater than "
                    "or equal to zero"
                )
        elif value <= 0:
            raise ValueError(
                "generation_duration_ns must be "
                "greater than zero"
            )

        return value
