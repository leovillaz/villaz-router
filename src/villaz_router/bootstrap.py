import os
from pathlib import Path

from pydantic import ValidationError

from villaz_router.bootstrap_errors import (
    ApplicationBootstrapError,
    ApplicationBootstrapErrorCode,
    BootstrapStage,
)
from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.errors import RouterError
from villaz_router.loader import load_ruleset_snapshot
from villaz_router.registry_errors import RegistryError
from villaz_router.registry_loader import (
    load_profile_registry_snapshot,
)
from villaz_router.runtime_compatibility import (
    validate_runtime_compatibility,
)
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
)


def _normalize_configuration_root(
    configuration_root: str | Path | None,
) -> Path:
    if configuration_root is None or configuration_root == "":
        raise ApplicationBootstrapError(
            code=ApplicationBootstrapErrorCode.ROOT_REQUIRED,
            stage=BootstrapStage.CONFIGURATION_ROOT,
            message="configuration_root is required",
        )

    root = Path(configuration_root).resolve()

    if not root.exists():
        raise ApplicationBootstrapError(
            code=ApplicationBootstrapErrorCode.ROOT_NOT_FOUND,
            stage=BootstrapStage.CONFIGURATION_ROOT,
            message=f"configuration_root does not exist: {root}",
        )

    if not root.is_dir():
        raise ApplicationBootstrapError(
            code=ApplicationBootstrapErrorCode.ROOT_NOT_DIRECTORY,
            stage=BootstrapStage.CONFIGURATION_ROOT,
            message=f"configuration_root is not a directory: {root}",
        )

    if not os.access(root, os.R_OK | os.X_OK):
        raise ApplicationBootstrapError(
            code=ApplicationBootstrapErrorCode.ROOT_NOT_READABLE,
            stage=BootstrapStage.CONFIGURATION_ROOT,
            message=f"configuration_root is not readable: {root}",
        )

    return root


def bootstrap_runtime(
    configuration_root: str | Path | None,
) -> RuntimeContext:
    root = _normalize_configuration_root(configuration_root)

    try:
        ruleset = load_ruleset_snapshot(root)
    except RouterError as exc:
        raise ApplicationBootstrapError(
            code=ApplicationBootstrapErrorCode.RULESET_LOAD_FAILED,
            stage=BootstrapStage.RULESET,
            message="unable to load ruleset",
            cause=exc,
        ) from exc

    try:
        registry = load_profile_registry_snapshot(root)
    except RegistryError as exc:
        raise ApplicationBootstrapError(
            code=(
                ApplicationBootstrapErrorCode
                .PROFILE_REGISTRY_LOAD_FAILED
            ),
            stage=BootstrapStage.PROFILE_REGISTRY,
            message="unable to load profile registry",
            cause=exc,
        ) from exc

    try:
        validate_runtime_compatibility(ruleset, registry)
    except RuntimeCompatibilityError as exc:
        raise ApplicationBootstrapError(
            code=(
                ApplicationBootstrapErrorCode
                .RUNTIME_COMPATIBILITY_FAILED
            ),
            stage=BootstrapStage.RUNTIME_COMPATIBILITY,
            message="runtime configuration is incompatible",
            cause=exc,
        ) from exc

    try:
        return RuntimeContext(
            configuration_root=root,
            ruleset=ruleset,
            profile_registry=registry,
        )
    except ValidationError as exc:
        raise ApplicationBootstrapError(
            code=(
                ApplicationBootstrapErrorCode
                .RUNTIME_CONTEXT_CREATION_FAILED
            ),
            stage=BootstrapStage.RUNTIME_CONTEXT,
            message="unable to create runtime context",
            cause=exc,
        ) from exc