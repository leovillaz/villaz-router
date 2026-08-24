from pydantic import ValidationError

from .dispatcher_errors import DispatcherError, DispatcherErrorCode
from .dispatcher_models import DispatchPlan
from .models import RouteDecision, RouteState
from .registry_errors import RegistryError, RegistryErrorCode
from .registry_models import ProfileRegistrySnapshot


def build_dispatch_plan(
    decision: RouteDecision,
    registry: ProfileRegistrySnapshot,
) -> DispatchPlan:
    if decision.state is RouteState.ROUTED:
        if decision.profile is None or decision.route_id is None:
            raise DispatcherError(
                DispatcherErrorCode.INVALID_ROUTE_DECISION,
                "route decision is structurally invalid for dispatch",
            )

    elif decision.state is RouteState.EXPLICIT:
        if decision.profile is None or decision.route_id is not None:
            raise DispatcherError(
                DispatcherErrorCode.INVALID_ROUTE_DECISION,
                "route decision is structurally invalid for dispatch",
            )

    else:
        raise DispatcherError(
            DispatcherErrorCode.NON_DISPATCHABLE_DECISION,
            f"route decision state '{decision.state.value}' is not dispatchable",
        )

    profile_id = decision.profile

    try:
        profile = registry.get(profile_id)
    except RegistryError as exc:
        if exc.code is RegistryErrorCode.PROFILE_NOT_FOUND:
            raise DispatcherError(
                DispatcherErrorCode.PROFILE_NOT_FOUND,
                f"profile '{profile_id}' was not found in registry",
            ) from exc
        raise

    if not profile.enabled:
        raise DispatcherError(
            DispatcherErrorCode.PROFILE_DISABLED,
            f"profile '{profile_id}' is disabled",
        )

    try:
        return DispatchPlan(
            profile_id=profile.id,
            model=profile.model,
            system_prompt=profile.system_prompt,
            registry_hash=registry.registry_hash,
            source_state=decision.state,
            route_id=decision.route_id,
        )
    except ValidationError as exc:
        raise DispatcherError(
            DispatcherErrorCode.INVALID_DISPATCH_PLAN,
            "unable to construct dispatch plan",
        ) from exc
