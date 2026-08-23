from villaz_router.errors import RouterError
from villaz_router.registry_errors import RegistryError, RegistryErrorCode


def test_registry_error_codes_are_stable() -> None:
    assert tuple(code.value for code in RegistryErrorCode) == (
        "INVALID_PROFILE_DEFINITION",
        "DUPLICATE_PROFILE_ID",
        "PROFILE_NOT_FOUND",
        "INVALID_REGISTRY",
    )


def test_registry_error_preserves_code_and_message() -> None:
    error = RegistryError(
        RegistryErrorCode.INVALID_REGISTRY,
        "registry failure",
    )

    assert error.code is RegistryErrorCode.INVALID_REGISTRY
    assert error.message == "registry failure"
    assert error.args == ("registry failure",)


def test_registry_error_string_representation() -> None:
    error = RegistryError(
        RegistryErrorCode.PROFILE_NOT_FOUND,
        "profile not found",
    )

    assert str(error) == "PROFILE_NOT_FOUND: profile not found"


def test_registry_error_is_not_a_router_error() -> None:
    assert not issubclass(RegistryError, RouterError)
