import pytest
from pydantic import ValidationError

from villaz_router.registry_errors import RegistryError, RegistryErrorCode
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)


def make_profile(profile_id: str, enabled: bool = True) -> ProfileDefinition:
    return ProfileDefinition(
        id=profile_id,
        enabled=enabled,
        display_name=profile_id,
        description=f"Profile {profile_id}",
        model="example-model:latest",
        system_prompt=f"Prompt for {profile_id}",
    )


def make_snapshot(**overrides) -> ProfileRegistrySnapshot:
    profiles = (
        make_profile("docs-dev"),
        make_profile("mobile-dev"),
    )
    data = {
        "profiles": profiles,
        "profile_ids": ("docs-dev", "mobile-dev"),
        "registry_hash": "a" * 64,
    }
    data.update(overrides)
    return ProfileRegistrySnapshot(**data)


def test_snapshot_accepts_valid_registry() -> None:
    snapshot = make_snapshot()

    assert snapshot.profile_ids == ("docs-dev", "mobile-dev")
    assert snapshot.registry_hash == "a" * 64


def test_snapshot_rejects_empty_profiles() -> None:
    with pytest.raises(ValidationError):
        make_snapshot(profiles=(), profile_ids=())


def test_snapshot_rejects_duplicate_profile_ids() -> None:
    profiles = (
        make_profile("docs-dev"),
        make_profile("docs-dev"),
    )

    with pytest.raises(ValidationError):
        make_snapshot(
            profiles=profiles,
            profile_ids=("docs-dev", "docs-dev"),
        )


def test_snapshot_requires_canonical_profile_order() -> None:
    profiles = (
        make_profile("mobile-dev"),
        make_profile("docs-dev"),
    )

    with pytest.raises(ValidationError):
        make_snapshot(
            profiles=profiles,
            profile_ids=("mobile-dev", "docs-dev"),
        )


def test_profile_ids_must_match_profiles_exactly() -> None:
    with pytest.raises(ValidationError):
        make_snapshot(profile_ids=("docs-dev",))


@pytest.mark.parametrize(
    "registry_hash",
    [
        "",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
    ],
)
def test_registry_hash_requires_lowercase_sha256_format(
    registry_hash: str,
) -> None:
    with pytest.raises(ValidationError):
        make_snapshot(registry_hash=registry_hash)


def test_get_returns_existing_profile() -> None:
    snapshot = make_snapshot()

    profile = snapshot.get("mobile-dev")

    assert profile.id == "mobile-dev"


def test_get_missing_profile_raises_registry_error() -> None:
    snapshot = make_snapshot()

    with pytest.raises(RegistryError) as exc_info:
        snapshot.get("unity-dev")

    assert exc_info.value.code is RegistryErrorCode.PROFILE_NOT_FOUND


def test_contains_uses_exact_profile_id() -> None:
    snapshot = make_snapshot()

    assert snapshot.contains("mobile-dev") is True
    assert snapshot.contains("Mobile-Dev") is False
    assert snapshot.contains(" mobile-dev") is False


def test_disabled_profile_still_exists_in_registry() -> None:
    profiles = (
        make_profile("docs-dev", enabled=False),
        make_profile("mobile-dev"),
    )
    snapshot = make_snapshot(
        profiles=profiles,
        profile_ids=("docs-dev", "mobile-dev"),
    )

    assert snapshot.contains("docs-dev") is True
    assert snapshot.get("docs-dev").enabled is False


def test_list_profiles_returns_canonical_tuple() -> None:
    snapshot = make_snapshot()

    assert snapshot.list_profiles() is snapshot.profiles


def test_snapshot_is_immutable() -> None:
    snapshot = make_snapshot()

    with pytest.raises(ValidationError):
        snapshot.registry_hash = "b" * 64


def test_snapshot_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        make_snapshot(source="file")
