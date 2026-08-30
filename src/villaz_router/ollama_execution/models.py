from pydantic import (
    BaseModel,
    ConfigDict,
    StrictStr,
    field_validator,
)

from villaz_router.dispatcher_models import DispatchPlan


class OllamaExecutionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    dispatch_plan: DispatchPlan
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
