from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    field_validator,
    model_validator,
)


class ProfileDefinition(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
    )

    id: StrictStr = Field(
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    enabled: StrictBool
    display_name: StrictStr
    description: StrictStr
    model: StrictStr
    system_prompt: StrictStr

    @field_validator(
        "display_name",
        "description",
        "model",
        "system_prompt",
    )
    @classmethod
    def validate_non_whitespace_text(
        cls,
        value: str,
    ) -> str:
        if value.strip() == "":
            raise ValueError(
                "value must contain at least one non-whitespace character"
            )

        return value


class ProfileRegistrySnapshot(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    profiles: tuple[ProfileDefinition, ...]
    profile_ids: tuple[str, ...]
    registry_hash: StrictStr = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    @field_validator("profiles")
    @classmethod
    def validate_profiles(
        cls,
        profiles: tuple[ProfileDefinition, ...],
    ) -> tuple[ProfileDefinition, ...]:
        if not profiles:
            raise ValueError("registry requires at least one profile")

        ids = tuple(profile.id for profile in profiles)

        if len(ids) != len(set(ids)):
            raise ValueError("registry profile ids must be unique")

        if ids != tuple(sorted(ids)):
            raise ValueError("registry profiles must be ordered by id")

        return profiles

    @field_validator("profile_ids")
    @classmethod
    def validate_profile_ids_not_empty(
        cls,
        profile_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if not profile_ids:
            raise ValueError("profile_ids must not be empty")

        return profile_ids

    @model_validator(mode="after")
    def validate_profile_ids_projection(self) -> "ProfileRegistrySnapshot":
        expected = tuple(profile.id for profile in self.profiles)
        if self.profile_ids != expected:
            raise ValueError("profile_ids must exactly match profiles")

        return self

    def get(self, profile_id: str) -> ProfileDefinition:
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile

        from villaz_router.registry_errors import (
            RegistryError,
            RegistryErrorCode,
        )

        raise RegistryError(
            RegistryErrorCode.PROFILE_NOT_FOUND,
            f"profile '{profile_id}' was not found",
        )

    def contains(self, profile_id: str) -> bool:
        return profile_id in self.profile_ids

    def list_profiles(self) -> tuple[ProfileDefinition, ...]:
        return self.profiles
