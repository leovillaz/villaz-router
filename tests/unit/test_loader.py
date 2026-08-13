from pathlib import Path

import pytest

from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.loader import load_ruleset_documents


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_loads_official_ruleset_documents() -> None:
    loaded = load_ruleset_documents(PROJECT_ROOT)

    assert loaded.config.schema_version == "1.0"
    assert loaded.profiles.ruleset_version == "1.0.0"
    assert loaded.domains.ruleset_version == "1.0.0"
    assert loaded.intents.ruleset_version == "1.0.0"
    assert loaded.routing.ruleset_version == "1.0.0"


def test_loads_expected_profiles() -> None:
    loaded = load_ruleset_documents(PROJECT_ROOT)

    profile_ids = tuple(
        profile.id
        for profile in loaded.profiles.profiles
    )

    assert profile_ids == (
        "mobile-dev",
        "unity-dev",
        "docs-dev",
        "fiscal-finance",
        "code-review-security",
    )


def test_loads_expected_routes() -> None:
    loaded = load_ruleset_documents(PROJECT_ROOT)

    routes = {
        route.id: route
        for route in loaded.routing.routes
    }

    assert routes["ROUTE-REVIEW-001"].priority == 500
    assert routes["ROUTE-FISCAL-001"].priority == 450
    assert routes["ROUTE-DOC-001"].priority == 400
    assert routes["ROUTE-UNITY-001"].priority == 300
    assert routes["ROUTE-MOBILE-001"].priority == 200


def test_missing_ruleset_file_is_invalid_ruleset(
    tmp_path: Path,
) -> None:
    with pytest.raises(RouterError) as exc_info:
        load_ruleset_documents(tmp_path)

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET


def test_invalid_yaml_is_invalid_ruleset(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    rules_dir = tmp_path / "rules"

    config_dir.mkdir()
    rules_dir.mkdir()

    (config_dir / "router.yaml").write_text(
        "router: [",
        encoding="utf-8",
    )

    with pytest.raises(RouterError) as exc_info:
        load_ruleset_documents(tmp_path)

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET


def test_non_mapping_document_is_invalid_ruleset(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    rules_dir = tmp_path / "rules"

    config_dir.mkdir()
    rules_dir.mkdir()

    (config_dir / "router.yaml").write_text(
        "- invalid\n- document\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError) as exc_info:
        load_ruleset_documents(tmp_path)

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET
