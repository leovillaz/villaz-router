from typing import Annotated
from urllib.parse import urlsplit

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


PositiveFiniteStrictFloat = Annotated[
    StrictFloat,
    Field(gt=0, allow_inf_nan=False),
]
PositiveStrictInt = Annotated[
    StrictInt,
    Field(gt=0),
]
NonNegativeStrictInt = Annotated[
    StrictInt,
    Field(ge=0),
]


class OllamaTimeoutConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )

    connect_seconds: PositiveFiniteStrictFloat
    read_seconds: PositiveFiniteStrictFloat
    write_seconds: PositiveFiniteStrictFloat
    pool_seconds: PositiveFiniteStrictFloat

    @field_validator(
        "connect_seconds",
        "read_seconds",
        "write_seconds",
        "pool_seconds",
        mode="before",
    )
    @classmethod
    def validate_strict_float(
        cls,
        value: object,
    ) -> object:
        if type(value) is not float:
            raise ValueError(
                "timeout value must be a float"
            )
        return value


class OllamaConnectionLimits(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )

    max_connections: PositiveStrictInt
    max_keepalive_connections: NonNegativeStrictInt
    keepalive_expiry_seconds: PositiveFiniteStrictFloat

    @field_validator(
        "keepalive_expiry_seconds",
        mode="before",
    )
    @classmethod
    def validate_strict_float(
        cls,
        value: object,
    ) -> object:
        if type(value) is not float:
            raise ValueError(
                "keepalive_expiry_seconds must be a float"
            )
        return value

    @model_validator(mode="after")
    def validate_connection_coherence(
        self,
    ) -> "OllamaConnectionLimits":
        if (
            self.max_keepalive_connections
            > self.max_connections
        ):
            raise ValueError(
                "max_keepalive_connections must not exceed "
                "max_connections"
            )

        return self


class OllamaClientConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    base_url: StrictStr
    timeouts: OllamaTimeoutConfig
    limits: OllamaConnectionLimits

    @field_validator("base_url")
    @classmethod
    def validate_base_url(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "base_url must not be empty or whitespace-only"
            )

        if any(
            character.isspace()
            for character in value
        ):
            raise ValueError(
                "base_url must not contain whitespace"
            )

        if "?" in value:
            raise ValueError(
                "base_url must not include a query"
            )

        if "#" in value:
            raise ValueError(
                "base_url must not include a fragment"
            )

        try:
            parsed = urlsplit(value)
            _ = parsed.port
        except ValueError as exc:
            raise ValueError(
                "base_url is invalid"
            ) from exc

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "base_url scheme must be http or https"
            )

        if parsed.hostname is None:
            raise ValueError(
                "base_url must include a host"
            )

        if (
            parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "base_url must not include credentials"
            )

        if parsed.netloc.endswith(":"):
            raise ValueError(
                "base_url contains an invalid port"
            )

        if parsed.path not in {"", "/"}:
            raise ValueError(
                "base_url must not include an operation path"
            )

        return value

    @field_validator("timeouts", mode="before")
    @classmethod
    def validate_timeouts_type(
        cls,
        value: object,
    ) -> object:
        if not isinstance(
            value,
            OllamaTimeoutConfig,
        ):
            raise ValueError(
                "timeouts must be an "
                "OllamaTimeoutConfig instance"
            )

        return value

    @field_validator("limits", mode="before")
    @classmethod
    def validate_limits_type(
        cls,
        value: object,
    ) -> object:
        if not isinstance(
            value,
            OllamaConnectionLimits,
        ):
            raise ValueError(
                "limits must be an "
                "OllamaConnectionLimits instance"
            )

        return value
