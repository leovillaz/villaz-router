from pathlib import Path

import pytest
import yaml

from villaz_router.registry_canonical import compute_registry_hash
from villaz_router.registry_errors import RegistryError, RegistryErrorCode
from villaz_router.registry_loader import load_profile_registry_snapshot


def profile_data(profile_id: str, **overrides):
    data = {
        "id": profile_id,
        "enabled": True,
        "display_name": f"Perfil {profile_id}",
        "description": f"Descrição de {profile_id}",
        "model": "modelo:latest",
        "system_prompt": f"Prompt para {profile_id}.",
    }
    data.update(overrides)
    return data


def write_registry(
    root: Path,
    document,
) -> Path:
    directory = root / "profiles"
    directory.mkdir(parents=True)
    path = directory / "profiles.yaml"
    path.write_text(
        yaml.safe_dump(
            document,
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def valid_document() -> dict:
    return {
        "schema_version": "1.0",
        "profiles": [
            profile_data("docs-dev"),
            profile_data("mobile-dev"),
        ],
    }


def test_load_valid_registry_snapshot(tmp_path: Path) -> None:
    write_registry(tmp_path, valid_document())

    snapshot = load_profile_registry_snapshot(tmp_path)

    assert snapshot.profile_ids == ("docs-dev", "mobile-dev")
    assert snapshot.contains("docs-dev") is True


def test_missing_registry_file_is_invalid_registry(
    tmp_path: Path,
) -> None:
    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


def test_invalid_yaml_is_invalid_registry(tmp_path: Path) -> None:
    directory = tmp_path / "profiles"
    directory.mkdir()
    path = directory / "profiles.yaml"
    path.write_text("profiles: [", encoding="utf-8")

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


@pytest.mark.parametrize("document", [None, [], "text", 1])
def test_non_mapping_document_is_invalid_registry(
    tmp_path: Path,
    document,
) -> None:
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


@pytest.mark.parametrize("schema_version", [None, 1.0, "", "2.0"])
def test_schema_version_must_be_supported_exactly(
    tmp_path: Path,
    schema_version,
) -> None:
    document = valid_document()
    document["schema_version"] = schema_version
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


def test_unexpected_top_level_field_is_invalid_registry(
    tmp_path: Path,
) -> None:
    document = valid_document()
    document["unexpected"] = True
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


@pytest.mark.parametrize("profiles", [None, {}, "profiles", ()])
def test_profiles_must_be_nonempty_list(
    tmp_path: Path,
    profiles,
) -> None:
    document = {
        "schema_version": "1.0",
        "profiles": profiles,
    }
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


def test_empty_profiles_list_is_invalid_registry(tmp_path: Path) -> None:
    write_registry(
        tmp_path,
        {"schema_version": "1.0", "profiles": []},
    )

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.INVALID_REGISTRY


def test_non_mapping_profile_is_invalid_profile_definition(
    tmp_path: Path,
) -> None:
    write_registry(
        tmp_path,
        {"schema_version": "1.0", "profiles": ["mobile-dev"]},
    )

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert (
        exc_info.value.code
        is RegistryErrorCode.INVALID_PROFILE_DEFINITION
    )


def test_invalid_profile_fields_are_invalid_profile_definition(
    tmp_path: Path,
) -> None:
    document = valid_document()
    document["profiles"][0]["model"] = "   "
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert (
        exc_info.value.code
        is RegistryErrorCode.INVALID_PROFILE_DEFINITION
    )


def test_unexpected_profile_field_is_invalid_profile_definition(
    tmp_path: Path,
) -> None:
    document = valid_document()
    document["profiles"][0]["temperature"] = 0.2
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert (
        exc_info.value.code
        is RegistryErrorCode.INVALID_PROFILE_DEFINITION
    )


def test_duplicate_profile_id_has_specific_error(
    tmp_path: Path,
) -> None:
    document = {
        "schema_version": "1.0",
        "profiles": [
            profile_data("mobile-dev"),
            profile_data("mobile-dev"),
        ],
    }
    write_registry(tmp_path, document)

    with pytest.raises(RegistryError) as exc_info:
        load_profile_registry_snapshot(tmp_path)

    assert exc_info.value.code is RegistryErrorCode.DUPLICATE_PROFILE_ID


def test_loader_canonicalizes_profile_source_order(
    tmp_path: Path,
) -> None:
    document = {
        "schema_version": "1.0",
        "profiles": [
            profile_data("unity-dev"),
            profile_data("docs-dev"),
            profile_data("mobile-dev"),
        ],
    }
    write_registry(tmp_path, document)

    snapshot = load_profile_registry_snapshot(tmp_path)

    assert snapshot.profile_ids == (
        "docs-dev",
        "mobile-dev",
        "unity-dev",
    )


def test_loader_uses_canonical_registry_hash(tmp_path: Path) -> None:
    write_registry(tmp_path, valid_document())

    snapshot = load_profile_registry_snapshot(tmp_path)

    assert snapshot.registry_hash == compute_registry_hash(
        "1.0",
        snapshot.profiles,
    )


def test_repeated_load_is_deterministic(tmp_path: Path) -> None:
    write_registry(tmp_path, valid_document())

    first = load_profile_registry_snapshot(tmp_path)
    second = load_profile_registry_snapshot(tmp_path)

    assert first == second
