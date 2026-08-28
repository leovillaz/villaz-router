from typing import NoReturn

from villaz_router.models import RulesetSnapshot
from villaz_router.registry_models import ProfileRegistrySnapshot
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
    RuntimeCompatibilityErrorCode,
    RuntimeCompatibilityReason,
)


def _raise_incompatibility(
    reason: RuntimeCompatibilityReason,
    profile_id: str,
    route_id: str | None = None,
) -> NoReturn:
    if reason is RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY:
        route_id = None
        message = f"profile '{profile_id}' is missing from registry"
    elif reason is RuntimeCompatibilityReason.PROFILE_EXTRA_IN_REGISTRY:
        route_id = None
        message = f"profile '{profile_id}' exists in registry but not in ruleset"
    elif reason is RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE:
        if route_id is None:
            raise ValueError(
                "route_id is required for ROUTE_REFERENCES_UNKNOWN_PROFILE"
            )
        message = f"route '{route_id}' references unknown profile '{profile_id}'"
    else:
        route_id = None
        message = (
            f"profile '{profile_id}' enabled state differs between ruleset and registry"
        )

    raise RuntimeCompatibilityError(
        code=RuntimeCompatibilityErrorCode.INCOMPATIBLE_RUNTIME_CONFIGURATION,
        reason=reason,
        profile_id=profile_id,
        route_id=route_id,
        message=message,
    )


def validate_runtime_compatibility(
    ruleset: RulesetSnapshot,
    registry: ProfileRegistrySnapshot,
) -> None:
    router_profiles_by_id = {
        profile.id: profile
        for profile in ruleset.profiles
    }
    registry_profiles_by_id = {
        profile.id: profile
        for profile in registry.profiles
    }

    for route in sorted(
        ruleset.routes,
        key=lambda item: (item.id, item.result.profile),
    ):
        profile_id = route.result.profile
        if profile_id not in router_profiles_by_id:
            _raise_incompatibility(
                RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE,
                profile_id=profile_id,
                route_id=route.id,
            )

    for profile in sorted(ruleset.profiles, key=lambda item: item.id):
        if profile.id not in registry_profiles_by_id:
            _raise_incompatibility(
                RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY,
                profile_id=profile.id,
            )

    for profile in sorted(registry.profiles, key=lambda item: item.id):
        if profile.id not in router_profiles_by_id:
            _raise_incompatibility(
                RuntimeCompatibilityReason.PROFILE_EXTRA_IN_REGISTRY,
                profile_id=profile.id,
            )

    for profile in sorted(ruleset.profiles, key=lambda item: item.id):
        registry_profile = registry_profiles_by_id[profile.id]
        if profile.enabled != registry_profile.enabled:
            _raise_incompatibility(
                RuntimeCompatibilityReason.PROFILE_ENABLED_MISMATCH,
                profile_id=profile.id,
            )

    return None
