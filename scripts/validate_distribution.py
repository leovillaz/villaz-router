import argparse
from configparser import ConfigParser
from pathlib import Path, PurePosixPath
import tarfile
import zipfile


RUNTIME_DATA_FILES = frozenset({
    "villaz_router/runtime_data/config/ollama.yaml",
    "villaz_router/runtime_data/config/router.yaml",
    "villaz_router/runtime_data/profiles/profiles.yaml",
    "villaz_router/runtime_data/rules/domains.yaml",
    "villaz_router/runtime_data/rules/intents.yaml",
    "villaz_router/runtime_data/rules/profiles.yaml",
    "villaz_router/runtime_data/rules/routing.yaml",
})

CANONICAL_CONFIGURATION_FILES = frozenset({
    "config/ollama.yaml",
    "config/router.yaml",
    "profiles/profiles.yaml",
    "rules/domains.yaml",
    "rules/intents.yaml",
    "rules/profiles.yaml",
    "rules/routing.yaml",
})

PUBLIC_DOCUMENTS = frozenset({
    "docs/API.md",
    "docs/ARCHITECTURE.md",
    "docs/CONFIGURATION.md",
    "docs/DEVELOPMENT.md",
    "docs/INSTALLATION.md",
    "docs/PROJECT_STATUS.md",
    "docs/REPLICATION_GUIDE.md",
    "docs/ROADMAP.md",
    "docs/ROUTER_007.md",
    "docs/RULESET_REFERENCE.md",
    "docs/TESTING.md",
    "docs/TROUBLESHOOTING.md",
})

WHEEL_REQUIRED = RUNTIME_DATA_FILES | {
    "villaz_router/__init__.py",
    "villaz_router/__main__.py",
    "villaz_router/cli.py",
    "villaz_router/runtime_resources.py",
}

SDIST_REQUIRED = (
    CANONICAL_CONFIGURATION_FILES
    | PUBLIC_DOCUMENTS
    | {
        "CONTRIBUTING.md",
        "LICENSE",
        "MANIFEST.in",
        "README.md",
        "SECURITY.md",
        "pyproject.toml",
        "src/villaz_router/__init__.py",
        "src/villaz_router/__main__.py",
        "src/villaz_router/cli.py",
        "src/villaz_router/runtime_resources.py",
    }
    | {
        f"src/{relative_path}"
        for relative_path in RUNTIME_DATA_FILES
    }
)

FORBIDDEN_PARTS = frozenset({
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
})


class DistributionValidationError(RuntimeError):
    pass


def _require_exactly_one(
    paths: list[Path],
    artifact_type: str,
) -> Path:
    if len(paths) != 1:
        raise DistributionValidationError(
            f"expected exactly one {artifact_type}, "
            f"found {len(paths)}"
        )
    return paths[0]


def _validate_member_names(
    member_names: set[str],
    artifact_type: str,
) -> None:
    for member_name in member_names:
        path = PurePosixPath(member_name)

        if path.is_absolute() or ".." in path.parts:
            raise DistributionValidationError(
                f"{artifact_type} contains unsafe path: "
                f"{member_name}"
            )

        if FORBIDDEN_PARTS.intersection(path.parts):
            raise DistributionValidationError(
                f"{artifact_type} contains forbidden path: "
                f"{member_name}"
            )

        if path.name == "AGENTS.md":
            raise DistributionValidationError(
                f"{artifact_type} contains AGENTS.md"
            )

        if path.suffix in {".pyc", ".pyo"}:
            raise DistributionValidationError(
                f"{artifact_type} contains bytecode: "
                f"{member_name}"
            )


def _require_members(
    actual: set[str],
    required: frozenset[str] | set[str],
    artifact_type: str,
) -> None:
    missing = sorted(required - actual)
    if missing:
        raise DistributionValidationError(
            f"{artifact_type} is missing required files: "
            + ", ".join(missing)
        )


def _validate_wheel(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as archive:
        members = {
            info.filename
            for info in archive.infolist()
            if not info.is_dir()
        }
        _validate_member_names(members, "wheel")
        _require_members(
            members,
            WHEEL_REQUIRED,
            "wheel",
        )

        packaged_resources = {
            name
            for name in members
            if name.startswith(
                "villaz_router/runtime_data/"
            )
            and name
            != "villaz_router/runtime_data/__init__.py"
        }
        if packaged_resources != RUNTIME_DATA_FILES:
            raise DistributionValidationError(
                "wheel runtime data differs from the "
                "exact approved set"
            )

        entry_point_files = sorted(
            name
            for name in members
            if name.endswith(
                ".dist-info/entry_points.txt"
            )
        )
        if len(entry_point_files) != 1:
            raise DistributionValidationError(
                "wheel must contain exactly one "
                "dist-info/entry_points.txt"
            )

        entry_points = ConfigParser(
            interpolation=None
        )
        entry_points.read_string(
            archive.read(
                entry_point_files[0]
            ).decode("utf-8")
        )
        if (
            not entry_points.has_section(
                "console_scripts"
            )
            or entry_points.get(
                "console_scripts",
                "villaz-router",
                fallback=None,
            )
            != "villaz_router.cli:main"
        ):
            raise DistributionValidationError(
                "wheel does not expose the villaz-router "
                "console entrypoint"
            )


def _validate_sdist(sdist_path: Path) -> None:
    with tarfile.open(sdist_path, mode="r:gz") as archive:
        raw_members = {
            name.rstrip("/")
            for name in archive.getnames()
            if name.rstrip("/")
        }

    _validate_member_names(raw_members, "sdist")

    roots = {
        PurePosixPath(name).parts[0]
        for name in raw_members
    }
    if len(roots) != 1:
        raise DistributionValidationError(
            "sdist must contain exactly one root directory"
        )

    relative_members = {
        "/".join(PurePosixPath(name).parts[1:])
        for name in raw_members
        if len(PurePosixPath(name).parts) > 1
    }
    _require_members(
        relative_members,
        SDIST_REQUIRED,
        "sdist",
    )


def validate_distribution(dist_directory: Path) -> None:
    if not dist_directory.is_dir():
        raise DistributionValidationError(
            f"distribution directory does not exist: "
            f"{dist_directory}"
        )

    wheel_path = _require_exactly_one(
        sorted(dist_directory.glob("*.whl")),
        "wheel",
    )
    sdist_path = _require_exactly_one(
        sorted(dist_directory.glob("*.tar.gz")),
        "sdist",
    )

    _validate_wheel(wheel_path)
    _validate_sdist(sdist_path)

    print(f"validated wheel: {wheel_path.name}")
    print(f"validated sdist: {sdist_path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Villaz Router wheel and sdist "
            "contents."
        )
    )
    parser.add_argument(
        "dist_directory",
        type=Path,
    )
    arguments = parser.parse_args()

    validate_distribution(
        arguments.dist_directory.resolve()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
