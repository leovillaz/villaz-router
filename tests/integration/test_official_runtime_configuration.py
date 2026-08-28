from pathlib import Path

from villaz_router import (
    load_profile_registry_snapshot,
    load_ruleset_snapshot,
    validate_runtime_compatibility,
)


ROOT = Path(__file__).resolve().parents[2]


EXPECTED_MODELS = {
    "code-review-security": "qwen2.5-coder:14b",
    "docs-dev": "gemma3:12b",
    "fiscal-finance": "qwen3:14b",
    "mobile-dev": "qwen2.5-coder:14b",
    "unity-dev": "qwen2.5-coder:14b",
}


def test_official_runtime_configuration_is_compatible() -> None:
    ruleset = load_ruleset_snapshot(ROOT)
    registry = load_profile_registry_snapshot(ROOT)

    validate_runtime_compatibility(ruleset, registry)

    profiles = registry.list_profiles()

    assert tuple(profile.id for profile in profiles) == tuple(EXPECTED_MODELS)
    assert all(profile.enabled for profile in profiles)
    assert {profile.id: profile.model for profile in profiles} == EXPECTED_MODELS
    assert all(profile.system_prompt for profile in profiles)
