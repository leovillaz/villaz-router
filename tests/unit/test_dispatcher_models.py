import pytest
from pydantic import ValidationError

from villaz_router.dispatcher_models import DispatchPlan
from villaz_router.models import RouteState


HASH = "a" * 64


def make_plan(**changes: object) -> DispatchPlan:
    data = {
        "profile_id": "mobile-dev",
        "model": "qwen3:8b",
        "system_prompt": "You are a mobile development assistant.",
        "registry_hash": HASH,
        "source_state": RouteState.ROUTED,
        "route_id": "ROUTE-MOBILE-001",
    }
    data.update(changes)
    return DispatchPlan(**data)


def test_routed_dispatch_plan_is_valid() -> None:
    plan = make_plan()
    assert plan.profile_id == "mobile-dev"
    assert plan.source_state is RouteState.ROUTED
    assert plan.route_id == "ROUTE-MOBILE-001"


def test_explicit_dispatch_plan_is_valid() -> None:
    plan = make_plan(source_state=RouteState.EXPLICIT, route_id=None)
    assert plan.source_state is RouteState.EXPLICIT
    assert plan.route_id is None


def test_dispatch_plan_is_frozen() -> None:
    plan = make_plan()
    with pytest.raises(ValidationError):
        plan.model = "other-model"


def test_dispatch_plan_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        make_plan(extra_field="invalid")


@pytest.mark.parametrize("field", ["profile_id", "model", "system_prompt"])
@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_required_text_rejects_empty_or_whitespace_only(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        make_plan(**{field: value})


def test_valid_whitespace_is_preserved_exactly() -> None:
    plan = make_plan(
        model="  qwen3:8b  ",
        system_prompt="  Keep these spaces.  ",
    )
    assert plan.model == "  qwen3:8b  "
    assert plan.system_prompt == "  Keep these spaces.  "


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
    ],
)
def test_registry_hash_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValidationError):
        make_plan(registry_hash=value)


@pytest.mark.parametrize("state", [RouteState.AMBIGUOUS, RouteState.UNROUTED])
def test_non_dispatchable_source_states_are_rejected(state: RouteState) -> None:
    with pytest.raises(ValidationError):
        make_plan(source_state=state)


def test_routed_requires_route_id() -> None:
    with pytest.raises(ValidationError):
        make_plan(route_id=None)


def test_explicit_requires_route_id_none() -> None:
    with pytest.raises(ValidationError):
        make_plan(source_state=RouteState.EXPLICIT, route_id="ROUTE-MOBILE-001")


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_route_id_rejects_empty_or_whitespace_only(value: str) -> None:
    with pytest.raises(ValidationError):
        make_plan(route_id=value)
