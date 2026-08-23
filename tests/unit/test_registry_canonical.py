import hashlib

import pytest

from villaz_router.registry_canonical import (
    canonical_registry_bytes,
    canonical_registry_json,
    canonical_registry_payload,
    compute_registry_hash,
    create_profile_registry_snapshot,
)
from villaz_router.registry_models import ProfileDefinition


def make_profile(
    profile_id: str,
    **overrides,
) -> ProfileDefinition:
    data = {
        "id": profile_id,
        "enabled": True,
        "display_name": f"Perfil {profile_id}",
        "description": f"Descrição de {profile_id}",
        "model": "modelo:latest",
        "system_prompt": f"Prompt para {profile_id}.",
    }
    data.update(overrides)
    return ProfileDefinition(**data)


def test_canonical_payload_has_fixed_top_level_order() -> None:
    payload = canonical_registry_payload(
        "1.0",
        (make_profile("mobile-dev"),),
    )

    assert tuple(payload) == ("schema_version", "profiles")


def test_canonical_profile_has_fixed_field_order() -> None:
    payload = canonical_registry_payload(
        "1.0",
        (make_profile("mobile-dev"),),
    )

    assert tuple(payload["profiles"][0]) == (
        "id",
        "enabled",
        "display_name",
        "description",
        "model",
        "system_prompt",
    )


def test_canonical_payload_orders_profiles_by_id() -> None:
    payload = canonical_registry_payload(
        "1.0",
        (
            make_profile("unity-dev"),
            make_profile("docs-dev"),
            make_profile("mobile-dev"),
        ),
    )

    assert [item["id"] for item in payload["profiles"]] == [
        "docs-dev",
        "mobile-dev",
        "unity-dev",
    ]


def test_canonical_json_is_compact_utf8_and_exact() -> None:
    profile = ProfileDefinition(
        id="docs-dev",
        enabled=True,
        display_name="Documentação",
        description="Perfil técnico",
        model="modelo:latest",
        system_prompt="Responda em PT-BR.",
    )

    result = canonical_registry_json("1.0", (profile,))

    assert result == (
        '{"schema_version":"1.0","profiles":[' 
        '{"id":"docs-dev","enabled":true,' 
        '"display_name":"Documentação",' 
        '"description":"Perfil técnico",' 
        '"model":"modelo:latest",' 
        '"system_prompt":"Responda em PT-BR."}]}' 
    )


def test_canonical_bytes_are_utf8_without_final_newline() -> None:
    profile = make_profile("docs-dev")
    result = canonical_registry_bytes("1.0", (profile,))

    assert result == canonical_registry_json(
        "1.0",
        (profile,),
    ).encode("utf-8")
    assert not result.endswith(b"\\n")


def test_registry_hash_matches_sha256_of_canonical_bytes() -> None:
    profiles = (make_profile("docs-dev"),)
    expected = hashlib.sha256(
        canonical_registry_bytes("1.0", profiles)
    ).hexdigest()

    assert compute_registry_hash("1.0", profiles) == expected


def test_profile_source_order_does_not_change_hash() -> None:
    docs = make_profile("docs-dev")
    mobile = make_profile("mobile-dev")

    first = compute_registry_hash("1.0", (docs, mobile))
    second = compute_registry_hash("1.0", (mobile, docs))

    assert first == second


@pytest.mark.parametrize(
    "field_name,new_value",
    [
        ("enabled", False),
        ("display_name", "Outro nome"),
        ("description", "Outra descrição"),
        ("model", "outro-modelo:latest"),
        ("system_prompt", "Outro prompt."),
    ],
)
def test_semantic_profile_change_changes_hash(
    field_name: str,
    new_value,
) -> None:
    original = make_profile("mobile-dev")
    changed = make_profile(
        "mobile-dev",
        **{field_name: new_value},
    )

    assert compute_registry_hash(
        "1.0",
        (original,),
    ) != compute_registry_hash(
        "1.0",
        (changed,),
    )


def test_schema_version_changes_hash() -> None:
    profiles = (make_profile("docs-dev"),)

    assert compute_registry_hash(
        "1.0",
        profiles,
    ) != compute_registry_hash(
        "2.0",
        profiles,
    )


def test_valid_whitespace_is_preserved_and_changes_hash() -> None:
    normal = make_profile(
        "docs-dev",
        description="Perfil técnico",
    )
    spaced = make_profile(
        "docs-dev",
        description="Perfil técnico ",
    )

    assert compute_registry_hash(
        "1.0",
        (normal,),
    ) != compute_registry_hash(
        "1.0",
        (spaced,),
    )


def test_unicode_is_not_ascii_escaped() -> None:
    profile = make_profile(
        "docs-dev",
        description="Documentação técnica",
    )

    result = canonical_registry_json("1.0", (profile,))

    assert "Documentação técnica" in result
    assert "\\\\u00e7" not in result


def test_create_snapshot_orders_profiles_and_derives_ids() -> None:
    snapshot = create_profile_registry_snapshot(
        "1.0",
        (
            make_profile("unity-dev"),
            make_profile("docs-dev"),
            make_profile("mobile-dev"),
        ),
    )

    assert snapshot.profile_ids == (
        "docs-dev",
        "mobile-dev",
        "unity-dev",
    )
    assert tuple(
        profile.id for profile in snapshot.profiles
    ) == snapshot.profile_ids


def test_create_snapshot_uses_registry_hash_contract() -> None:
    profiles = (
        make_profile("docs-dev"),
        make_profile("mobile-dev"),
    )
    snapshot = create_profile_registry_snapshot(
        "1.0",
        profiles,
    )

    assert snapshot.registry_hash == compute_registry_hash(
        "1.0",
        profiles,
    )


def test_registry_hash_is_repeatable() -> None:
    profiles = (
        make_profile("docs-dev"),
        make_profile("mobile-dev"),
    )

    assert compute_registry_hash(
        "1.0",
        profiles,
    ) == compute_registry_hash(
        "1.0",
        profiles,
    )
