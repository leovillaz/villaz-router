from pathlib import Path

import villaz_router
from villaz_router import (
    ApplicationBootstrapError,
    ApplicationBootstrapErrorCode,
    BootstrapStage,
    RuntimeContext,
    bootstrap_runtime,
)

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_REGISTRY_HASH = (
    "c9b7ef321815b11f6a38fcd0c4b3538b"
    "c549e78a41a1149760e3c49f8dcbf6af"
)

EXPECTED_MODELS = {
    "code-review-security": "qwen2.5-coder:14b",
    "docs-dev": "gemma3:12b",
    "fiscal-finance": "qwen3:14b",
    "mobile-dev": "qwen2.5-coder:14b",
    "unity-dev": "qwen2.5-coder:14b",
}


def test_application_bootstrap_symbols_are_public() -> None:
    expected_exports = {
        "ApplicationBootstrapError",
        "ApplicationBootstrapErrorCode",
        "BootstrapStage",
        "RuntimeContext",
        "bootstrap_runtime",
    }

    assert expected_exports <= set(villaz_router.__all__)
    assert (
        villaz_router.ApplicationBootstrapError
        is ApplicationBootstrapError
    )
    assert (
        villaz_router.ApplicationBootstrapErrorCode
        is ApplicationBootstrapErrorCode
    )
    assert villaz_router.BootstrapStage is BootstrapStage
    assert villaz_router.RuntimeContext is RuntimeContext
    assert villaz_router.bootstrap_runtime is bootstrap_runtime


def test_official_application_bootstrap_succeeds() -> None:
    context = bootstrap_runtime(ROOT)

    assert isinstance(context, RuntimeContext)
    assert context.configuration_root == ROOT

    assert len(context.ruleset.ruleset_hash) == 64
    int(context.ruleset.ruleset_hash, 16)

    registry = context.profile_registry

    assert registry.registry_hash == EXPECTED_REGISTRY_HASH
    assert registry.profile_ids == tuple(EXPECTED_MODELS)
    assert all(profile.enabled for profile in registry.profiles)
    assert {
        profile.id: profile.model
        for profile in registry.profiles
    } == EXPECTED_MODELS
    assert all(
        profile.system_prompt
        for profile in registry.profiles
    )