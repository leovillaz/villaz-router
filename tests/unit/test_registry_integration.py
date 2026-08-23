from pathlib import Path

from villaz_router.registry_loader import load_profile_registry_snapshot


PROFILE_DOCS = """schema_version: "1.0"
profiles:
  - id: docs-dev
    enabled: true
    display_name: Documentação
    description: Perfil de documentação técnica.
    model: modelo:latest
    system_prompt: Responda como especialista em documentação.
  - id: mobile-dev
    enabled: false
    display_name: Mobile
    description: Perfil mobile.
    model: modelo:latest
    system_prompt: Responda como especialista mobile.
"""


PROFILE_DOCS_REORDERED = """profiles:
  - system_prompt: Responda como especialista mobile.
    model: modelo:latest
    description: Perfil mobile.
    display_name: Mobile
    enabled: false
    id: mobile-dev
  - description: Perfil de documentação técnica.
    system_prompt: Responda como especialista em documentação.
    id: docs-dev
    model: modelo:latest
    enabled: true
    display_name: Documentação
schema_version: "1.0"
"""


def write_registry(root: Path, text: str) -> None:
    directory = root / "profiles"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "profiles.yaml").write_text(
        text,
        encoding="utf-8",
    )


def test_full_registry_flow(tmp_path: Path) -> None:
    write_registry(tmp_path, PROFILE_DOCS)

    snapshot = load_profile_registry_snapshot(tmp_path)

    assert snapshot.profile_ids == ("docs-dev", "mobile-dev")
    assert snapshot.get("docs-dev").enabled is True
    assert snapshot.get("mobile-dev").enabled is False
    assert snapshot.contains("docs-dev") is True
    assert snapshot.contains("unknown-dev") is False
    assert snapshot.list_profiles() == snapshot.profiles


def test_yaml_physical_order_does_not_change_registry_hash(
    tmp_path: Path,
) -> None:
    write_registry(tmp_path, PROFILE_DOCS)
    first = load_profile_registry_snapshot(tmp_path)

    write_registry(tmp_path, PROFILE_DOCS_REORDERED)
    second = load_profile_registry_snapshot(tmp_path)

    assert first.registry_hash == second.registry_hash
    assert first == second


def test_semantic_yaml_change_changes_registry_hash(
    tmp_path: Path,
) -> None:
    write_registry(tmp_path, PROFILE_DOCS)
    first = load_profile_registry_snapshot(tmp_path)

    changed = PROFILE_DOCS.replace(
        "Perfil mobile.",
        "Perfil mobile alterado.",
    )
    write_registry(tmp_path, changed)
    second = load_profile_registry_snapshot(tmp_path)

    assert first.registry_hash != second.registry_hash
    assert first != second


def test_snapshot_preserves_exact_valid_text(
    tmp_path: Path,
) -> None:
    text = PROFILE_DOCS.replace(
        "description: Perfil mobile.",
        'description: " Perfil mobile. "',
    )
    write_registry(tmp_path, text)

    snapshot = load_profile_registry_snapshot(tmp_path)

    assert snapshot.get("mobile-dev").description == " Perfil mobile. "
