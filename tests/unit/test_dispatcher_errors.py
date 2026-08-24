from villaz_router.dispatcher_errors import DispatcherError, DispatcherErrorCode
from villaz_router.errors import RouterError
from villaz_router.registry_errors import RegistryError


def test_dispatcher_error_codes_are_exact() -> None:
    assert tuple(code.value for code in DispatcherErrorCode) == (
        "INVALID_ROUTE_DECISION",
        "NON_DISPATCHABLE_DECISION",
        "PROFILE_NOT_FOUND",
        "PROFILE_DISABLED",
        "INVALID_DISPATCH_PLAN",
    )


def test_dispatcher_error_exposes_code_message_args_and_string() -> None:
    error = DispatcherError(
        DispatcherErrorCode.PROFILE_DISABLED,
        "profile 'mobile-dev' is disabled",
    )

    assert error.code is DispatcherErrorCode.PROFILE_DISABLED
    assert error.message == "profile 'mobile-dev' is disabled"
    assert error.args == ("profile 'mobile-dev' is disabled",)
    assert str(error) == "PROFILE_DISABLED: profile 'mobile-dev' is disabled"


def test_dispatcher_error_does_not_inherit_router_error() -> None:
    assert not issubclass(DispatcherError, RouterError)


def test_dispatcher_error_does_not_inherit_registry_error() -> None:
    assert not issubclass(DispatcherError, RegistryError)
