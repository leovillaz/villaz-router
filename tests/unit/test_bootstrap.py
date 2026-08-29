from pathlib import Path

import pytest
from pydantic import ValidationError

import villaz_router.bootstrap as bootstrap_module
from villaz_router.bootstrap import bootstrap_runtime
from villaz_router.bootstrap_errors import (
    ApplicationBootstrapError,
    ApplicationBootstrapErrorCode,
    BootstrapStage,
)
from villaz_router.bootstrap_models import (
    RuntimeContext as RuntimeContextModel,
)
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.models import RulesetSnapshot
from villaz_router.registry_errors import (
    RegistryError,
    RegistryErrorCode,
)
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
    RuntimeCompatibilityErrorCode,
    RuntimeCompatibilityReason,
)


def make_ruleset_snapshot() -> RulesetSnapshot:
    return RulesetSnapshot.model_construct()


def make_profile_registry_snapshot() -> ProfileRegistrySnapshot:
    profile = ProfileDefinition(
        id="mobile-dev",
        enabled=True,
        display_name="Mobile Development",
        description="Profile for mobile development",
        model="example-model:latest",
        system_prompt="Develop mobile applications.",
    )

    return ProfileRegistrySnapshot(
        profiles=(profile,),
        profile_ids=(profile.id,),
        registry_hash="a" * 64,
    )


@pytest.mark.parametrize("configuration_root", [None, ""])
def test_configuration_root_is_required(
    configuration_root: str | None,
) -> None:
    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(configuration_root)

    error = exc_info.value

    assert error.code is ApplicationBootstrapErrorCode.ROOT_REQUIRED
    assert error.stage is BootstrapStage.CONFIGURATION_ROOT
    assert error.message == "configuration_root is required"
    assert error.cause is None


def test_configuration_root_must_exist(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(missing)

    error = exc_info.value

    assert error.code is ApplicationBootstrapErrorCode.ROOT_NOT_FOUND
    assert error.stage is BootstrapStage.CONFIGURATION_ROOT
    assert error.message == (
        f"configuration_root does not exist: {missing.resolve()}"
    )
    assert error.cause is None


def test_configuration_root_must_be_directory(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "configuration.txt"
    file_path.write_text("configuration", encoding="utf-8")

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(file_path)

    error = exc_info.value

    assert (
        error.code
        is ApplicationBootstrapErrorCode.ROOT_NOT_DIRECTORY
    )
    assert error.stage is BootstrapStage.CONFIGURATION_ROOT
    assert error.message == (
        f"configuration_root is not a directory: "
        f"{file_path.resolve()}"
    )
    assert error.cause is None


def test_configuration_root_must_be_readable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bootstrap_module.os,
        "access",
        lambda path, mode: False,
    )

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(tmp_path)

    error = exc_info.value

    assert error.code is ApplicationBootstrapErrorCode.ROOT_NOT_READABLE
    assert error.stage is BootstrapStage.CONFIGURATION_ROOT
    assert error.message == (
        f"configuration_root is not readable: {tmp_path.resolve()}"
    )
    assert error.cause is None


def test_bootstrap_executes_stages_in_order_and_returns_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ruleset = make_ruleset_snapshot()
    registry = make_profile_registry_snapshot()
    calls: list[str] = []

    monkeypatch.chdir(tmp_path.parent)
    relative_root = Path(tmp_path.name)
    expected_root = tmp_path.resolve()

    def fake_load_ruleset(root: Path) -> RulesetSnapshot:
        calls.append("ruleset")
        assert root == expected_root
        return ruleset

    def fake_load_registry(root: Path) -> ProfileRegistrySnapshot:
        calls.append("registry")
        assert root == expected_root
        return registry

    def fake_validate_runtime(
        received_ruleset: RulesetSnapshot,
        received_registry: ProfileRegistrySnapshot,
    ) -> None:
        calls.append("compatibility")
        assert received_ruleset is ruleset
        assert received_registry is registry

    monkeypatch.setattr(
        bootstrap_module,
        "load_ruleset_snapshot",
        fake_load_ruleset,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "load_profile_registry_snapshot",
        fake_load_registry,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "validate_runtime_compatibility",
        fake_validate_runtime,
    )

    context = bootstrap_runtime(relative_root)

    assert calls == [
        "ruleset",
        "registry",
        "compatibility",
    ]
    assert context.configuration_root == expected_root
    assert context.ruleset is ruleset
    assert context.profile_registry is registry


def test_ruleset_failure_stops_bootstrap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_error = RouterError(
        RouterErrorCode.INVALID_RULESET,
        "invalid ruleset",
    )
    calls: list[str] = []

    def fail_ruleset(root: Path) -> RulesetSnapshot:
        calls.append("ruleset")
        raise original_error

    def forbidden_stage(*args: object) -> None:
        calls.append("forbidden")
        raise AssertionError("later stage must not execute")

    monkeypatch.setattr(
        bootstrap_module,
        "load_ruleset_snapshot",
        fail_ruleset,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "load_profile_registry_snapshot",
        forbidden_stage,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "validate_runtime_compatibility",
        forbidden_stage,
    )

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(tmp_path)

    error = exc_info.value

    assert calls == ["ruleset"]
    assert (
        error.code
        is ApplicationBootstrapErrorCode.RULESET_LOAD_FAILED
    )
    assert error.stage is BootstrapStage.RULESET
    assert error.cause is original_error
    assert error.__cause__ is original_error


def test_registry_failure_stops_bootstrap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ruleset = make_ruleset_snapshot()
    original_error = RegistryError(
        RegistryErrorCode.INVALID_REGISTRY,
        "invalid registry",
    )
    calls: list[str] = []

    def load_ruleset(root: Path) -> RulesetSnapshot:
        calls.append("ruleset")
        return ruleset

    def fail_registry(root: Path) -> ProfileRegistrySnapshot:
        calls.append("registry")
        raise original_error

    def forbidden_stage(*args: object) -> None:
        calls.append("forbidden")
        raise AssertionError("later stage must not execute")

    monkeypatch.setattr(
        bootstrap_module,
        "load_ruleset_snapshot",
        load_ruleset,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "load_profile_registry_snapshot",
        fail_registry,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "validate_runtime_compatibility",
        forbidden_stage,
    )

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(tmp_path)

    error = exc_info.value

    assert calls == ["ruleset", "registry"]
    assert (
        error.code
        is ApplicationBootstrapErrorCode.PROFILE_REGISTRY_LOAD_FAILED
    )
    assert error.stage is BootstrapStage.PROFILE_REGISTRY
    assert error.cause is original_error
    assert error.__cause__ is original_error


def test_compatibility_failure_stops_before_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ruleset = make_ruleset_snapshot()
    registry = make_profile_registry_snapshot()
    original_error = RuntimeCompatibilityError(
        code=(
            RuntimeCompatibilityErrorCode
            .INCOMPATIBLE_RUNTIME_CONFIGURATION
        ),
        reason=(
            RuntimeCompatibilityReason
            .PROFILE_MISSING_FROM_REGISTRY
        ),
        profile_id="mobile-dev",
        route_id=None,
        message="profile 'mobile-dev' is missing from registry",
    )
    calls: list[str] = []

    def load_ruleset(root: Path) -> RulesetSnapshot:
        calls.append("ruleset")
        return ruleset

    def load_registry(root: Path) -> ProfileRegistrySnapshot:
        calls.append("registry")
        return registry

    def fail_compatibility(
        received_ruleset: RulesetSnapshot,
        received_registry: ProfileRegistrySnapshot,
    ) -> None:
        calls.append("compatibility")
        raise original_error

    def forbidden_context(**kwargs: object) -> None:
        calls.append("context")
        raise AssertionError("context must not be created")

    monkeypatch.setattr(
        bootstrap_module,
        "load_ruleset_snapshot",
        load_ruleset,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "load_profile_registry_snapshot",
        load_registry,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "validate_runtime_compatibility",
        fail_compatibility,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "RuntimeContext",
        forbidden_context,
    )

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(tmp_path)

    error = exc_info.value

    assert calls == [
        "ruleset",
        "registry",
        "compatibility",
    ]
    assert (
        error.code
        is ApplicationBootstrapErrorCode.RUNTIME_COMPATIBILITY_FAILED
    )
    assert error.stage is BootstrapStage.RUNTIME_COMPATIBILITY
    assert error.cause is original_error
    assert error.__cause__ is original_error


def test_context_validation_failure_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ruleset = make_ruleset_snapshot()
    registry = make_profile_registry_snapshot()

    monkeypatch.setattr(
        bootstrap_module,
        "load_ruleset_snapshot",
        lambda root: ruleset,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "load_profile_registry_snapshot",
        lambda root: registry,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "validate_runtime_compatibility",
        lambda received_ruleset, received_registry: None,
    )

    def fail_context(**kwargs: object) -> RuntimeContextModel:
        return RuntimeContextModel.model_validate({})

    monkeypatch.setattr(
        bootstrap_module,
        "RuntimeContext",
        fail_context,
    )

    with pytest.raises(ApplicationBootstrapError) as exc_info:
        bootstrap_runtime(tmp_path)

    error = exc_info.value

    assert (
        error.code
        is ApplicationBootstrapErrorCode.RUNTIME_CONTEXT_CREATION_FAILED
    )
    assert error.stage is BootstrapStage.RUNTIME_CONTEXT
    assert isinstance(error.cause, ValidationError)
    assert error.__cause__ is error.cause


def test_unexpected_errors_are_not_masked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_error = RuntimeError("unexpected programming failure")

    def fail_unexpectedly(root: Path) -> RulesetSnapshot:
        raise original_error

    monkeypatch.setattr(
        bootstrap_module,
        "load_ruleset_snapshot",
        fail_unexpectedly,
    )

    with pytest.raises(RuntimeError) as exc_info:
        bootstrap_runtime(tmp_path)

    assert exc_info.value is original_error