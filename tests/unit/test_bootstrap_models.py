from pathlib import Path

import pytest
from pydantic import ValidationError

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.models import RulesetSnapshot
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)


def make_ruleset_snapshot() -> RulesetSnapshot:
    return RulesetSnapshot.model_construct()


def make_profile_registry_snapshot() -> ProfileRegistrySnapshot:
    profile = ProfileDefinition(
        id="mobile-dev",
        enabled=True,
        display_name="Mobile Development",
        description="Profile for mobile development",
        model="example-model:latest",
        system_prompt="Develop mobile applications.",
    )

    return ProfileRegistrySnapshot(
        profiles=(profile,),
        profile_ids=(profile.id,),
        registry_hash="a" * 64,
    )


def make_runtime_context(root: Path) -> RuntimeContext:
    return RuntimeContext(
        configuration_root=root,
        ruleset=make_ruleset_snapshot(),
        profile_registry=make_profile_registry_snapshot(),
    )


def test_runtime_context_has_exact_fields() -> None:
    assert tuple(RuntimeContext.model_fields) == (
        "configuration_root",
        "ruleset",
        "profile_registry",
    )


def test_runtime_context_preserves_snapshot_identity(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    ruleset = make_ruleset_snapshot()
    registry = make_profile_registry_snapshot()

    context = RuntimeContext(
        configuration_root=root,
        ruleset=ruleset,
        profile_registry=registry,
    )

    assert context.configuration_root == root
    assert context.ruleset is ruleset
    assert context.profile_registry is registry


def test_runtime_context_is_frozen(tmp_path: Path) -> None:
    context = make_runtime_context(tmp_path.resolve())

    with pytest.raises(ValidationError) as exc_info:
        context.configuration_root = tmp_path / "other"

    assert exc_info.value.errors()[0]["type"] == "frozen_instance"


def test_runtime_context_forbids_extra_fields(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        RuntimeContext(
            configuration_root=tmp_path.resolve(),
            ruleset=make_ruleset_snapshot(),
            profile_registry=make_profile_registry_snapshot(),
            is_ready=True,
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"


def test_runtime_context_rejects_invalid_snapshot_types(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValidationError):
        RuntimeContext(
            configuration_root=tmp_path.resolve(),
            ruleset="not-a-ruleset",
            profile_registry="not-a-registry",
        )
