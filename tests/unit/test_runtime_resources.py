import inspect
from importlib.resources import files
from pathlib import Path
import tomllib

import villaz_router.runtime_data as runtime_data
import pytest
from villaz_router.runtime_resources import (
    packaged_configuration_root,
)


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FILES = (
    "config/ollama.yaml",
    "config/router.yaml",
    "profiles/profiles.yaml",
    "rules/domains.yaml",
    "rules/intents.yaml",
    "rules/profiles.yaml",
    "rules/routing.yaml",
)


def test_runtime_data_contains_exact_canonical_files() -> None:
    resource_root = files(runtime_data)
    root_entries = {
        entry.name
        for entry in resource_root.iterdir()
        if entry.name != "__pycache__"
    }
    discovered = tuple(
        sorted(
            str(path.relative_to(resource_root)).replace(
                "\\",
                "/",
            )
            for directory in resource_root.iterdir()
            if directory.is_dir()
            and directory.name != "__pycache__"
            for path in directory.iterdir()
            if path.is_file()
        )
    )

    assert root_entries == {
        "__init__.py",
        "config",
        "profiles",
        "rules",
    }
    assert discovered == EXPECTED_FILES


def test_packaged_files_match_canonical_logical_content() -> None:
    resource_root = files(runtime_data)

    for relative_path in EXPECTED_FILES:
        resource = resource_root.joinpath(relative_path)
        canonical = ROOT / relative_path

        assert resource.read_text(encoding="utf-8").splitlines() == (
            canonical.read_text(encoding="utf-8").splitlines()
        )


def test_package_data_is_declared_explicitly() -> None:
    document = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    assert document["tool"]["setuptools"][
        "package-data"
    ] == {
        "villaz_router.runtime_data": [
            "config/*.yaml",
            "profiles/*.yaml",
            "rules/*.yaml",
        ]
    }


def test_packaged_root_is_absolute_and_independent_of_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    with packaged_configuration_root() as root:
        assert root.is_absolute()
        assert root != tmp_path
        for relative_path in EXPECTED_FILES:
            assert (root / relative_path).is_file()


def test_resolver_has_no_cwd_git_or_filesystem_search() -> None:
    source = inspect.getsource(
        packaged_configuration_root
    )

    assert "cwd" not in source
    assert ".git" not in source
    assert "parents" not in source
