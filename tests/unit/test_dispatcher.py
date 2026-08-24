import pytest
from pydantic import ValidationError

from villaz_router.dispatcher import build_dispatch_plan
from villaz_router.dispatcher_errors import DispatcherError, DispatcherErrorCode
from villaz_router.models import (
    RouteCandidate,
    RouteDecision,
    RouteState,
    RoutingMode,
    RoutingReason,
)
from villaz_router.registry_errors import RegistryError, RegistryErrorCode
from villaz_router.registry_models import ProfileDefinition, ProfileRegistrySnapshot


HASH = "a" * 64


def make_profile(enabled: bool = True) -> ProfileDefinition:
    return ProfileDefinition(
        id="mobile-dev",
        enabled=enabled,
        display_name="Mobile Dev",
        description="Mobile development profile",
        model="qwen3:8b",
        system_prompt="You are a mobile development assistant.",
    )


def make_registry(enabled: bool = True) -> ProfileRegistrySnapshot:
    profile = make_profile(enabled=enabled)
    return ProfileRegistrySnapshot(
        profiles=(profile,),
        profile_ids=(profile.id,),
        registry_hash=HASH,
    )


def make_routed_decision() -> RouteDecision:
    return RouteDecision(
        state=RouteState.ROUTED,
        profile="mobile-dev",
        route_id="ROUTE-MOBILE-001",
        comparison_score=10,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.MOBILE_DETECTED,
        conflict_resolved=False,
        candidates=(),
    )


def make_explicit_decision() -> RouteDecision:
    return RouteDecision(
        state=RouteState.EXPLICIT,
        profile="mobile-dev",
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.MANUAL,
        reason=RoutingReason.USER_SELECTED_PROFILE,
        conflict_resolved=False,
        candidates=(),
    )


def test_routed_decision_builds_dispatch_plan() -> None:
    plan = build_dispatch_plan(make_routed_decision(), make_registry())

    assert plan.profile_id == "mobile-dev"
    assert plan.model == "qwen3:8b"
    assert plan.system_prompt == "You are a mobile development assistant."
    assert plan.registry_hash == HASH
    assert plan.source_state is RouteState.ROUTED
    assert plan.route_id == "ROUTE-MOBILE-001"


def test_explicit_decision_builds_dispatch_plan() -> None:
    plan = build_dispatch_plan(make_explicit_decision(), make_registry())

    assert plan.profile_id == "mobile-dev"
    assert plan.source_state is RouteState.EXPLICIT
    assert plan.route_id is None


def test_profile_values_are_copied_exactly() -> None:
    profile = ProfileDefinition(
        id="mobile-dev",
        enabled=True,
        display_name="Mobile Dev",
        description="Mobile development profile",
        model="  qwen3:8b  ",
        system_prompt="  Preserve this prompt exactly.  ",
    )
    registry = ProfileRegistrySnapshot(
        profiles=(profile,),
        profile_ids=(profile.id,),
        registry_hash=HASH,
    )

    plan = build_dispatch_plan(make_routed_decision(), registry)

    assert plan.model == "  qwen3:8b  "
    assert plan.system_prompt == "  Preserve this prompt exactly.  "


def test_ambiguous_decision_is_not_dispatchable() -> None:
    decision = RouteDecision(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        candidates=(
            RouteCandidate(route_id="A", profile="mobile-dev", comparison_score=10),
            RouteCandidate(route_id="B", profile="docs-dev", comparison_score=10),
        ),
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.NON_DISPATCHABLE_DECISION
    assert exc_info.value.message == "route decision state 'ambiguous' is not dispatchable"


def test_unrouted_decision_is_not_dispatchable() -> None:
    decision = RouteDecision(
        state=RouteState.UNROUTED,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.INSUFFICIENT_EVIDENCE,
        candidates=(),
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.NON_DISPATCHABLE_DECISION
    assert exc_info.value.message == "route decision state 'unrouted' is not dispatchable"


def test_missing_profile_is_translated_to_dispatcher_error() -> None:
    decision = make_routed_decision().model_copy(update={"profile": "docs-dev"})

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.PROFILE_NOT_FOUND
    assert exc_info.value.message == "profile 'docs-dev' was not found in registry"
    assert exc_info.value.__cause__ is not None


def test_disabled_profile_is_rejected() -> None:
    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(make_routed_decision(), make_registry(enabled=False))

    assert exc_info.value.code is DispatcherErrorCode.PROFILE_DISABLED
    assert exc_info.value.message == "profile 'mobile-dev' is disabled"
    assert exc_info.value.__cause__ is None


def test_malformed_routed_decision_is_rejected_before_registry_resolution() -> None:
    decision = RouteDecision.model_construct(
        state=RouteState.ROUTED,
        profile="mobile-dev",
        route_id=None,
        comparison_score=10,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.MOBILE_DETECTED,
        conflict_resolved=False,
        candidates=(),
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.INVALID_ROUTE_DECISION
    assert exc_info.value.message == "route decision is structurally invalid for dispatch"


def test_malformed_explicit_decision_is_rejected_before_registry_resolution() -> None:
    decision = RouteDecision.model_construct(
        state=RouteState.EXPLICIT,
        profile="mobile-dev",
        route_id="ROUTE-MOBILE-001",
        comparison_score=None,
        mode=RoutingMode.MANUAL,
        reason=RoutingReason.USER_SELECTED_PROFILE,
        conflict_resolved=False,
        candidates=(),
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.INVALID_ROUTE_DECISION


def test_identical_inputs_produce_identical_plans() -> None:
    decision = make_routed_decision()
    registry = make_registry()

    first = build_dispatch_plan(decision, registry)
    second = build_dispatch_plan(decision, registry)

    assert first == second

def test_ambiguous_decision_does_not_consult_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = RouteDecision(
        state=RouteState.AMBIGUOUS,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.AMBIGUOUS_ROUTE,
        candidates=(
            RouteCandidate(route_id="A", profile="mobile-dev", comparison_score=10),
            RouteCandidate(route_id="B", profile="docs-dev", comparison_score=10),
        ),
    )

    def fail_get(self: ProfileRegistrySnapshot, profile_id: str) -> ProfileDefinition:
        raise AssertionError("registry must not be consulted")

    monkeypatch.setattr(ProfileRegistrySnapshot, "get", fail_get)

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.NON_DISPATCHABLE_DECISION


def test_unrouted_decision_does_not_consult_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = RouteDecision(
        state=RouteState.UNROUTED,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.INSUFFICIENT_EVIDENCE,
        candidates=(),
    )

    def fail_get(self: ProfileRegistrySnapshot, profile_id: str) -> ProfileDefinition:
        raise AssertionError("registry must not be consulted")

    monkeypatch.setattr(ProfileRegistrySnapshot, "get", fail_get)

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.NON_DISPATCHABLE_DECISION


def test_routed_without_profile_is_invalid_route_decision() -> None:
    decision = RouteDecision.model_construct(
        state=RouteState.ROUTED,
        profile=None,
        route_id="ROUTE-MOBILE-001",
        comparison_score=10,
        mode=RoutingMode.AUTO,
        reason=RoutingReason.MOBILE_DETECTED,
        conflict_resolved=False,
        candidates=(),
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.INVALID_ROUTE_DECISION


def test_explicit_without_profile_is_invalid_route_decision() -> None:
    decision = RouteDecision.model_construct(
        state=RouteState.EXPLICIT,
        profile=None,
        route_id=None,
        comparison_score=None,
        mode=RoutingMode.MANUAL,
        reason=RoutingReason.USER_SELECTED_PROFILE,
        conflict_resolved=False,
        candidates=(),
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    assert exc_info.value.code is DispatcherErrorCode.INVALID_ROUTE_DECISION


def test_missing_profile_preserves_registry_error_as_cause() -> None:
    decision = make_routed_decision().model_copy(update={"profile": "docs-dev"})

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(decision, make_registry())

    cause = exc_info.value.__cause__
    assert isinstance(cause, RegistryError)
    assert cause.code is RegistryErrorCode.PROFILE_NOT_FOUND


def test_unrelated_registry_error_propagates_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    original = RegistryError(
        RegistryErrorCode.INVALID_REGISTRY,
        "registry integrity failure",
    )

    def fail_get(self: ProfileRegistrySnapshot, profile_id: str) -> ProfileDefinition:
        raise original

    monkeypatch.setattr(ProfileRegistrySnapshot, "get", fail_get)

    with pytest.raises(RegistryError) as exc_info:
        build_dispatch_plan(make_routed_decision(), make_registry())

    assert exc_info.value is original


def test_invalid_final_plan_is_translated_to_dispatcher_error() -> None:
    profile = make_profile()
    registry = ProfileRegistrySnapshot.model_construct(
        profiles=(profile,),
        profile_ids=(profile.id,),
        registry_hash="invalid-hash",
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(make_routed_decision(), registry)

    assert exc_info.value.code is DispatcherErrorCode.INVALID_DISPATCH_PLAN
    assert exc_info.value.message == "unable to construct dispatch plan"
    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_unexpected_registry_exception_is_not_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_get(self: ProfileRegistrySnapshot, profile_id: str) -> ProfileDefinition:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(ProfileRegistrySnapshot, "get", fail_get)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        build_dispatch_plan(make_routed_decision(), make_registry())


def test_disabled_profile_does_not_fallback_to_another_profile() -> None:
    mobile = make_profile(enabled=False)
    unity = ProfileDefinition(
        id="unity-dev",
        enabled=True,
        display_name="Unity Dev",
        description="Unity development profile",
        model="unity-model",
        system_prompt="Unity assistant.",
    )
    registry = ProfileRegistrySnapshot(
        profiles=(mobile, unity),
        profile_ids=("mobile-dev", "unity-dev"),
        registry_hash=HASH,
    )

    with pytest.raises(DispatcherError) as exc_info:
        build_dispatch_plan(make_routed_decision(), registry)

    assert exc_info.value.code is DispatcherErrorCode.PROFILE_DISABLED

def test_dispatcher_public_api_is_exported_from_package() -> None:
    import villaz_router

    assert villaz_router.build_dispatch_plan is build_dispatch_plan
    assert villaz_router.DispatcherError is DispatcherError
    assert villaz_router.DispatcherErrorCode is DispatcherErrorCode
    from villaz_router.dispatcher_models import DispatchPlan
    assert villaz_router.DispatchPlan is DispatchPlan


def test_router_and_registry_modules_do_not_depend_on_dispatcher() -> None:
    from pathlib import Path

    package_dir = Path("src/villaz_router")
    forbidden_modules = {
        "dispatcher",
        "dispatcher_errors",
        "dispatcher_models",
    }
    protected_files = (
        package_dir / "router.py",
        package_dir / "registry_models.py",
        package_dir / "registry_errors.py",
        package_dir / "registry_canonical.py",
        package_dir / "registry_loader.py",
    )

    for path in protected_files:
        source = path.read_text()
        for module in forbidden_modules:
            assert f"villaz_router.{module}" not in source
            assert f"from .{module}" not in source
