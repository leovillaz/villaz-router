import copy

import pytest

from villaz_router.config import (
    AmbiguityConfig,
    CanonicalFormat,
    EligibilityConfig,
    EngineConfig,
    IntegrityAlgorithm,
    IntegrityConfig,
    LifecycleConfig,
    NormalizationConfig,
    PrivacyConfig,
    RouterSettings,
    RulesetReloadMode,
    ScoringConfig,
)
from villaz_router.models import (
    Profile,
    Route,
    RouteCondition,
    RouteResult,
    RulesetSnapshot,
)
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)
from villaz_router.runtime_compatibility import validate_runtime_compatibility
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
    RuntimeCompatibilityErrorCode,
    RuntimeCompatibilityReason,
)

HASH = "a" * 64


def make_router_settings() -> RouterSettings:
    return RouterSettings(
        engine=EngineConfig(expected_major_version=1),
        scoring=ScoringConfig(strong=10, medium=4, weak=1),
        eligibility=EligibilityConfig(
            minimum_score=10,
            weak_only_cannot_qualify=True,
        ),
        ambiguity=AmbiguityConfig(minimum_margin=5),
        normalization=NormalizationConfig(
            unicode_nfkc=True,
            lowercase=True,
            lowercase_locale_independent=True,
            collapse_whitespace=True,
            accent_insensitive_matching=True,
        ),
        lifecycle=LifecycleConfig(
            ruleset_reload=RulesetReloadMode.STARTUP_ONLY,
            immutable_snapshot_per_instance=True,
        ),
        integrity=IntegrityConfig(
            algorithm=IntegrityAlgorithm.SHA256,
            canonical_format=CanonicalFormat.DETERMINISTIC_JSON_UTF8,
        ),
        privacy=PrivacyConfig(
            store_full_message=False,
            store_evidence=False,
        ),
    )


def make_router_profile(
    profile_id: str,
    enabled: bool = True,
) -> Profile:
    return Profile(
        id=profile_id,
        enabled=enabled,
    )


def make_registry_profile(
    profile_id: str,
    enabled: bool = True,
) -> ProfileDefinition:
    return ProfileDefinition(
        id=profile_id,
        enabled=enabled,
        display_name=profile_id,
        description=f"Profile {profile_id}",
        model="example-model:latest",
        system_prompt=f"Prompt for {profile_id}",
    )


def make_route(
    route_id: str,
    profile_id: str,
    enabled: bool = True,
) -> Route:
    return Route(
        id=route_id,
        enabled=enabled,
        priority=100,
        when=RouteCondition(domain="mobile"),
        result=RouteResult(profile=profile_id),
    )


def make_ruleset(
    *,
    profiles: tuple[Profile, ...] | None = None,
    routes: tuple[Route, ...] | None = None,
) -> RulesetSnapshot:
    if profiles is None:
        profiles = (
            make_router_profile("docs-dev"),
            make_router_profile("mobile-dev"),
        )

    if routes is None:
        routes = (
            make_route("ROUTE-DOCS-001", "docs-dev"),
            make_route("ROUTE-MOBILE-001", "mobile-dev"),
        )

    return RulesetSnapshot(
        schema_version="1.0",
        ruleset_version="1.0.0",
        ruleset_hash=HASH,
        router=make_router_settings(),
        profiles=profiles,
        domains=(),
        intents=(),
        routes=routes,
    )


def make_registry(
    *,
    profiles: tuple[ProfileDefinition, ...] | None = None,
) -> ProfileRegistrySnapshot:
    if profiles is None:
        profiles = (
            make_registry_profile("docs-dev"),
            make_registry_profile("mobile-dev"),
        )

    canonical_profiles = tuple(
        sorted(
            profiles,
            key=lambda profile: profile.id,
        )
    )

    return ProfileRegistrySnapshot(
        profiles=canonical_profiles,
        profile_ids=tuple(
            profile.id
            for profile in canonical_profiles
        ),
        registry_hash=HASH,
    )


def assert_runtime_error(
    exc_info: pytest.ExceptionInfo[RuntimeCompatibilityError],
    *,
    reason: RuntimeCompatibilityReason,
    profile_id: str,
    message: str,
    route_id: str | None = None,
) -> None:
    error = exc_info.value

    assert (
        error.code
        is RuntimeCompatibilityErrorCode.INCOMPATIBLE_RUNTIME_CONFIGURATION
    )
    assert error.reason is reason
    assert error.profile_id == profile_id
    assert error.route_id == route_id
    assert error.message == message


def test_fully_compatible_snapshots_return_none() -> None:
    result = validate_runtime_compatibility(
        make_ruleset(),
        make_registry(),
    )

    assert result is None


def test_profile_missing_from_registry() -> None:
    ruleset = make_ruleset()
    registry = make_registry(
        profiles=(make_registry_profile("docs-dev"),),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert_runtime_error(
        exc_info,
        reason=RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY,
        profile_id="mobile-dev",
        message="profile 'mobile-dev' is missing from registry",
    )


def test_profile_extra_in_registry() -> None:
    ruleset = make_ruleset(
        profiles=(make_router_profile("docs-dev"),),
        routes=(make_route("ROUTE-DOCS-001", "docs-dev"),),
    )
    registry = make_registry(
        profiles=(
            make_registry_profile("docs-dev"),
            make_registry_profile("mobile-dev"),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert_runtime_error(
        exc_info,
        reason=RuntimeCompatibilityReason.PROFILE_EXTRA_IN_REGISTRY,
        profile_id="mobile-dev",
        message="profile 'mobile-dev' exists in registry but not in ruleset",
    )


def test_route_references_unknown_profile() -> None:
    ruleset = make_ruleset(
        routes=(
            make_route(
                "ROUTE-MOBILE-001",
                "unknown-profile",
            ),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(
            ruleset,
            make_registry(),
        )

    assert_runtime_error(
        exc_info,
        reason=RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE,
        profile_id="unknown-profile",
        route_id="ROUTE-MOBILE-001",
        message=(
            "route 'ROUTE-MOBILE-001' references unknown profile "
            "'unknown-profile'"
        ),
    )


def test_profile_enabled_mismatch() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("docs-dev"),
            make_router_profile("mobile-dev", enabled=False),
        ),
    )
    registry = make_registry()

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert_runtime_error(
        exc_info,
        reason=RuntimeCompatibilityReason.PROFILE_ENABLED_MISMATCH,
        profile_id="mobile-dev",
        message=(
            "profile 'mobile-dev' enabled state differs between ruleset "
            "and registry"
        ),
    )


def test_route_id_is_none_for_non_route_errors() -> None:
    ruleset = make_ruleset()
    registry = make_registry(
        profiles=(make_registry_profile("docs-dev"),),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.route_id is None


def test_disabled_route_with_unknown_profile_still_fails() -> None:
    ruleset = make_ruleset(
        routes=(
            make_route(
                "ROUTE-DISABLED-001",
                "unknown-profile",
                enabled=False,
            ),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(
            ruleset,
            make_registry(),
        )

    assert_runtime_error(
        exc_info,
        reason=RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE,
        profile_id="unknown-profile",
        route_id="ROUTE-DISABLED-001",
        message=(
            "route 'ROUTE-DISABLED-001' references unknown profile "
            "'unknown-profile'"
        ),
    )


def test_route_enabled_does_not_affect_profile_enabled_comparison() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("docs-dev"),
            make_router_profile("mobile-dev", enabled=False),
        ),
        routes=(
            make_route(
                "ROUTE-MOBILE-001",
                "mobile-dev",
                enabled=False,
            ),
        ),
    )
    registry = make_registry()

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_ENABLED_MISMATCH
    assert exc_info.value.profile_id == "mobile-dev"


def test_multiple_invalid_routes_choose_smallest_route_id() -> None:
    ruleset = make_ruleset(
        routes=(
            make_route("ROUTE-ZZZ-001", "unknown-z"),
            make_route("ROUTE-AAA-001", "unknown-a"),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(
            ruleset,
            make_registry(),
        )

    assert exc_info.value.reason is RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE
    assert exc_info.value.route_id == "ROUTE-AAA-001"
    assert exc_info.value.profile_id == "unknown-a"


def test_multiple_missing_profiles_choose_smallest_profile_id() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("zeta-dev"),
            make_router_profile("alpha-dev"),
        ),
        routes=(),
    )
    registry = make_registry(
        profiles=(make_registry_profile("zeta-dev"),),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY
    assert exc_info.value.profile_id == "alpha-dev"


def test_multiple_extra_profiles_choose_smallest_profile_id() -> None:
    ruleset = make_ruleset(
        profiles=(make_router_profile("docs-dev"),),
        routes=(),
    )
    registry = make_registry(
        profiles=(
            make_registry_profile("docs-dev"),
            make_registry_profile("mobile-dev"),
            make_registry_profile("unity-dev"),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_EXTRA_IN_REGISTRY
    assert exc_info.value.profile_id == "mobile-dev"


def test_multiple_enabled_mismatches_choose_smallest_profile_id() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("zeta-dev", enabled=False),
            make_router_profile("alpha-dev", enabled=False),
        ),
        routes=(),
    )
    registry = make_registry(
        profiles=(
            make_registry_profile("alpha-dev"),
            make_registry_profile("zeta-dev"),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_ENABLED_MISMATCH
    assert exc_info.value.profile_id == "alpha-dev"


def test_route_unknown_wins_over_missing_profile() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("docs-dev"),
            make_router_profile("mobile-dev"),
        ),
        routes=(make_route("ROUTE-A-001", "unknown-profile"),),
    )
    registry = make_registry(
        profiles=(make_registry_profile("docs-dev"),),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE


def test_missing_profile_wins_over_extra_profile() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("docs-dev"),
            make_router_profile("mobile-dev"),
        ),
        routes=(),
    )
    registry = make_registry(
        profiles=(
            make_registry_profile("docs-dev"),
            make_registry_profile("unity-dev"),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY
    assert exc_info.value.profile_id == "mobile-dev"


def test_extra_profile_wins_over_enabled_mismatch() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("docs-dev", enabled=False),
            make_router_profile("mobile-dev"),
        ),
        routes=(),
    )
    registry = make_registry(
        profiles=(
            make_registry_profile("docs-dev", enabled=True),
            make_registry_profile("mobile-dev"),
            make_registry_profile("unity-dev"),
        ),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_EXTRA_IN_REGISTRY
    assert exc_info.value.profile_id == "unity-dev"


def test_enabled_mismatch_is_checked_only_after_one_to_one_catalog() -> None:
    ruleset = make_ruleset(
        profiles=(
            make_router_profile("docs-dev", enabled=False),
            make_router_profile("mobile-dev"),
        ),
        routes=(),
    )
    registry = make_registry(
        profiles=(make_registry_profile("docs-dev", enabled=True),),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.PROFILE_MISSING_FROM_REGISTRY
    assert exc_info.value.profile_id == "mobile-dev"


def test_ruleset_profile_physical_order_does_not_change_result() -> None:
    registry = make_registry()

    first = make_ruleset(
        profiles=(
            make_router_profile("docs-dev"),
            make_router_profile("mobile-dev"),
        ),
        routes=(),
    )
    second = make_ruleset(
        profiles=(
            make_router_profile("mobile-dev"),
            make_router_profile("docs-dev"),
        ),
        routes=(),
    )

    assert validate_runtime_compatibility(first, registry) is None
    assert validate_runtime_compatibility(second, registry) is None


def test_route_physical_order_does_not_change_selected_error() -> None:
    first = make_ruleset(
        routes=(
            make_route("ROUTE-ZZZ-001", "unknown-z"),
            make_route("ROUTE-AAA-001", "unknown-a"),
        ),
    )
    second = make_ruleset(
        routes=tuple(reversed(first.routes)),
    )

    errors: list[RuntimeCompatibilityError] = []

    for ruleset in (first, second):
        with pytest.raises(RuntimeCompatibilityError) as exc_info:
            validate_runtime_compatibility(
                ruleset,
                make_registry(),
            )
        errors.append(exc_info.value)

    assert errors[0].reason is errors[1].reason
    assert errors[0].route_id == errors[1].route_id == "ROUTE-AAA-001"
    assert errors[0].profile_id == errors[1].profile_id == "unknown-a"
    assert errors[0].message == errors[1].message


def test_exact_ids_are_used_without_normalization() -> None:
    ruleset = make_ruleset(
        profiles=(make_router_profile("mobile-dev"),),
        routes=(make_route("ROUTE-MOBILE-001", "Mobile-Dev"),),
    )
    registry = make_registry(
        profiles=(make_registry_profile("mobile-dev"),),
    )

    with pytest.raises(RuntimeCompatibilityError) as exc_info:
        validate_runtime_compatibility(ruleset, registry)

    assert exc_info.value.reason is RuntimeCompatibilityReason.ROUTE_REFERENCES_UNKNOWN_PROFILE
    assert exc_info.value.profile_id == "Mobile-Dev"


def test_ruleset_snapshot_is_not_modified() -> None:
    ruleset = make_ruleset()
    registry = make_registry()
    before = copy.deepcopy(ruleset)

    validate_runtime_compatibility(ruleset, registry)

    assert ruleset == before


def test_registry_snapshot_is_not_modified() -> None:
    ruleset = make_ruleset()
    registry = make_registry()
    before = copy.deepcopy(registry)

    validate_runtime_compatibility(ruleset, registry)

    assert registry == before


def test_repeated_compatible_calls_are_deterministic() -> None:
    ruleset = make_ruleset()
    registry = make_registry()

    first = validate_runtime_compatibility(ruleset, registry)
    second = validate_runtime_compatibility(ruleset, registry)

    assert first is None
    assert second is None


def test_repeated_incompatible_calls_produce_same_error() -> None:
    ruleset = make_ruleset(
        routes=(
            make_route("ROUTE-ZZZ-001", "unknown-z"),
            make_route("ROUTE-AAA-001", "unknown-a"),
        ),
    )
    registry = make_registry()
    errors: list[RuntimeCompatibilityError] = []

    for _ in range(2):
        with pytest.raises(RuntimeCompatibilityError) as exc_info:
            validate_runtime_compatibility(ruleset, registry)
        errors.append(exc_info.value)

    assert errors[0].code is errors[1].code
    assert errors[0].reason is errors[1].reason
    assert errors[0].profile_id == errors[1].profile_id
    assert errors[0].route_id == errors[1].route_id
    assert errors[0].message == errors[1].message
