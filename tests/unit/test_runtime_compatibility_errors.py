from villaz_router.dispatcher_errors import DispatcherError
from villaz_router.errors import RouterError
from villaz_router.registry_errors import RegistryError
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
    RuntimeCompatibilityErrorCode,
    RuntimeCompatibilityReason,
)


def test_error_code_has_exact_value() -> None:
    assert [item.value for item in RuntimeCompatibilityErrorCode] == [
        "INCOMPATIBLE_RUNTIME_CONFIGURATION"
    ]


def test_reasons_have_exact_values() -> None:
    assert [item.value for item in RuntimeCompatibilityReason] == [
        "PROFILE_MISSING_FROM_REGISTRY",
        "PROFILE_EXTRA_IN_REGISTRY",
        "ROUTE_REFERENCES_UNKNOWN_PROFILE",
        "PROFILE_ENABLED_MISMATCH",
    ]


def test_error_exposes_structured_attributes() -> None:
    error = RuntimeCompatibilityError(
        code=RuntimeCompatibilityErrorCode.INCOMPATIBLE_RUNTIME_CONFIGURATION,
        reason=RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY,
        profile_id="mobile-dev",
        route_id=None,
        message="profile 'mobile-dev' is missing from registry",
    )

    assert error.code is RuntimeCompatibilityErrorCode.INCOMPATIBLE_RUNTIME_CONFIGURATION
    assert error.reason is RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY
    assert error.profile_id == "mobile-dev"
    assert error.route_id is None
    assert error.message == "profile 'mobile-dev' is missing from registry"
    assert error.args == ("profile 'mobile-dev' is missing from registry",)

    assert str(error) == (
        "INCOMPATIBLE_RUNTIME_CONFIGURATION: "
        "profile 'mobile-dev' is missing from registry"
    )


def test_error_is_independent_from_other_error_domains() -> None:
    assert not issubclass(RuntimeCompatibilityError, RouterError)
    assert not issubclass(RuntimeCompatibilityError, RegistryError)
    assert not issubclass(RuntimeCompatibilityError, DispatcherError)
