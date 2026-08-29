from villaz_router.bootstrap_errors import (
    ApplicationBootstrapError,
    ApplicationBootstrapErrorCode,
    BootstrapStage,
)
from villaz_router.dispatcher_errors import DispatcherError
from villaz_router.errors import RouterError
from villaz_router.registry_errors import RegistryError
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
)


def test_bootstrap_stages_have_exact_values() -> None:
    assert [item.value for item in BootstrapStage] == [
        "CONFIGURATION_ROOT",
        "RULESET",
        "PROFILE_REGISTRY",
        "RUNTIME_COMPATIBILITY",
        "RUNTIME_CONTEXT",
    ]


def test_bootstrap_error_codes_have_exact_values() -> None:
    assert [item.value for item in ApplicationBootstrapErrorCode] == [
        "ROOT_REQUIRED",
        "ROOT_NOT_FOUND",
        "ROOT_NOT_DIRECTORY",
        "ROOT_NOT_READABLE",
        "RULESET_LOAD_FAILED",
        "PROFILE_REGISTRY_LOAD_FAILED",
        "RUNTIME_COMPATIBILITY_FAILED",
        "RUNTIME_CONTEXT_CREATION_FAILED",
    ]


def test_error_exposes_structured_attributes() -> None:
    cause = RuntimeError("original failure")
    error = ApplicationBootstrapError(
        code=ApplicationBootstrapErrorCode.PROFILE_REGISTRY_LOAD_FAILED,
        stage=BootstrapStage.PROFILE_REGISTRY,
        message="unable to load profile registry",
        cause=cause,
    )

    assert (
        error.code
        is ApplicationBootstrapErrorCode.PROFILE_REGISTRY_LOAD_FAILED
    )
    assert error.stage is BootstrapStage.PROFILE_REGISTRY
    assert error.message == "unable to load profile registry"
    assert error.cause is cause
    assert error.args == ("unable to load profile registry",)
    assert str(error) == (
        "PROFILE_REGISTRY_LOAD_FAILED: "
        "unable to load profile registry"
    )


def test_error_cause_defaults_to_none() -> None:
    error = ApplicationBootstrapError(
        code=ApplicationBootstrapErrorCode.ROOT_REQUIRED,
        stage=BootstrapStage.CONFIGURATION_ROOT,
        message="configuration_root is required",
    )

    assert error.cause is None


def test_error_is_independent_from_existing_error_domains() -> None:
    assert not issubclass(ApplicationBootstrapError, RouterError)
    assert not issubclass(ApplicationBootstrapError, RegistryError)
    assert not issubclass(
        ApplicationBootstrapError,
        RuntimeCompatibilityError,
    )
    assert not issubclass(ApplicationBootstrapError, DispatcherError)
