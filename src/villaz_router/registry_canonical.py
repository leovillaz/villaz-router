from __future__ import annotations

import hashlib
import json
from typing import Any

from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)


def _canonical_profile(
    profile: ProfileDefinition,
) -> dict[str, Any]:
    return {
        "id": profile.id,
        "enabled": profile.enabled,
        "display_name": profile.display_name,
        "description": profile.description,
        "model": profile.model,
        "system_prompt": profile.system_prompt,
    }


def canonical_registry_payload(
    schema_version: str,
    profiles: tuple[ProfileDefinition, ...],
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "profiles": [
            _canonical_profile(profile)
            for profile in sorted(
                profiles,
                key=lambda item: item.id,
            )
        ],
    }


def canonical_registry_json(
    schema_version: str,
    profiles: tuple[ProfileDefinition, ...],
) -> str:
    payload = canonical_registry_payload(
        schema_version,
        profiles,
    )

    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
        allow_nan=False,
    )


def canonical_registry_bytes(
    schema_version: str,
    profiles: tuple[ProfileDefinition, ...],
) -> bytes:
    return canonical_registry_json(
        schema_version,
        profiles,
    ).encode("utf-8")


def compute_registry_hash(
    schema_version: str,
    profiles: tuple[ProfileDefinition, ...],
) -> str:
    return hashlib.sha256(
        canonical_registry_bytes(
            schema_version,
            profiles,
        )
    ).hexdigest()


def create_profile_registry_snapshot(
    schema_version: str,
    profiles: tuple[ProfileDefinition, ...],
) -> ProfileRegistrySnapshot:
    canonical_profiles = tuple(
        sorted(
            profiles,
            key=lambda item: item.id,
        )
    )

    return ProfileRegistrySnapshot(
        profiles=canonical_profiles,
        profile_ids=tuple(
            profile.id
            for profile in canonical_profiles
        ),
        registry_hash=compute_registry_hash(
            schema_version,
            canonical_profiles,
        ),
    )
