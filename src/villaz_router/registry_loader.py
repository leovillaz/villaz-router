from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from villaz_router.registry_canonical import (
    create_profile_registry_snapshot,
)
from villaz_router.registry_errors import (
    RegistryError,
    RegistryErrorCode,
)
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)


_SUPPORTED_SCHEMA_VERSION = "1.0"
_TOP_LEVEL_FIELDS = frozenset({
    "schema_version",
    "profiles",
})


def _invalid_registry(message: str) -> RegistryError:
    return RegistryError(
        RegistryErrorCode.INVALID_REGISTRY,
        message,
    )


def _read_registry_yaml(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise _invalid_registry(
            f"required registry file not found: {path}"
        ) from exc
    except OSError as exc:
        raise _invalid_registry(
            f"unable to read registry file: {path}"
        ) from exc

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise _invalid_registry(
            f"invalid YAML syntax: {path}"
        ) from exc


def _validate_global_structure(
    raw: Any,
    path: Path,
) -> tuple[str, list[Any]]:
    if not isinstance(raw, dict):
        raise _invalid_registry(
            f"registry document must be a mapping: {path}"
        )

    unknown_fields = tuple(
        sorted(set(raw) - _TOP_LEVEL_FIELDS)
    )
    if unknown_fields:
        raise _invalid_registry(
            "registry document contains unexpected fields: "
            + ", ".join(unknown_fields)
        )

    schema_version = raw.get("schema_version")
    if schema_version != _SUPPORTED_SCHEMA_VERSION:
        raise _invalid_registry(
            "registry schema_version must be "
            f"{_SUPPORTED_SCHEMA_VERSION!r}"
        )

    profiles = raw.get("profiles")
    if not isinstance(profiles, list):
        raise _invalid_registry(
            f"registry profiles must be a list: {path}"
        )

    if not profiles:
        raise _invalid_registry(
            f"registry requires at least one profile: {path}"
        )

    return schema_version, profiles


def _parse_profile_definition(
    raw: Any,
    index: int,
    path: Path,
) -> ProfileDefinition:
    if not isinstance(raw, dict):
        raise RegistryError(
            RegistryErrorCode.INVALID_PROFILE_DEFINITION,
            f"profile at index {index} must be a mapping: {path}",
        )

    profile_id = raw.get("id")
    context = (
        repr(profile_id)
        if isinstance(profile_id, str)
        else f"index {index}"
    )

    try:
        return ProfileDefinition.model_validate(raw)
    except ValidationError as exc:
        raise RegistryError(
            RegistryErrorCode.INVALID_PROFILE_DEFINITION,
            f"invalid profile definition {context}: {path}",
        ) from exc


def _reject_duplicate_profile_ids(
    profiles: tuple[ProfileDefinition, ...],
) -> None:
    seen: set[str] = set()

    for profile in profiles:
        if profile.id in seen:
            raise RegistryError(
                RegistryErrorCode.DUPLICATE_PROFILE_ID,
                f"duplicate profile id {profile.id!r}",
            )
        seen.add(profile.id)


def load_profile_registry_snapshot(
    project_root: Path,
) -> ProfileRegistrySnapshot:
    root = project_root.resolve()
    path = root / "profiles" / "profiles.yaml"

    raw = _read_registry_yaml(path)
    schema_version, raw_profiles = _validate_global_structure(
        raw,
        path,
    )

    profiles = tuple(
        _parse_profile_definition(item, index, path)
        for index, item in enumerate(raw_profiles)
    )

    _reject_duplicate_profile_ids(profiles)

    try:
        return create_profile_registry_snapshot(
            schema_version,
            profiles,
        )
    except ValidationError as exc:
        raise _invalid_registry(
            "unable to construct profile registry snapshot"
        ) from exc
