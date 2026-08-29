from pathlib import Path

from pydantic import BaseModel, ConfigDict

from villaz_router.models import RulesetSnapshot
from villaz_router.registry_models import ProfileRegistrySnapshot


class RuntimeContext(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    configuration_root: Path
    ruleset: RulesetSnapshot
    profile_registry: ProfileRegistrySnapshot
