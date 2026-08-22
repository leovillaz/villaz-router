import json
from pathlib import Path

import pytest

from villaz_router.errors import RouterError
from villaz_router.loader import load_ruleset_snapshot
from villaz_router.models import RouteRequest
from villaz_router.router import decide_route


MATRIX_PATH = Path(__file__).with_name("router_v1_cases.json")


def _matrix_cases() -> list[dict[str, object]]:
    document = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    return document["cases"]


@pytest.fixture(scope="module")
def snapshot():
    return load_ruleset_snapshot(Path.cwd())


@pytest.mark.parametrize(
    "case",
    _matrix_cases(),
    ids=lambda case: case["id"],
)
def test_router_behavior_matches_normative_matrix(case, snapshot) -> None:
    requested_profile = case["requested_profile"]

    request = RouteRequest(
        message=case["message"],
        explicit_profile=(
            None
            if requested_profile == "auto"
            else requested_profile
        ),
    )

    expected_error = case["expected_error"]
    repetitions = case["repetitions"]

    if expected_error is not None:
        observed_errors = []

        for _ in range(repetitions):
            with pytest.raises(RouterError) as exc_info:
                decide_route(request, snapshot)

            observed_errors.append(exc_info.value.code.value)

        assert observed_errors == [expected_error] * repetitions
        return

    observed_decisions = [
        decide_route(request, snapshot)
        for _ in range(repetitions)
    ]

    first = observed_decisions[0]

    assert first.state.value == case["expected_state"]
    assert first.profile == case["expected_profile"]
    assert first.reason.value == case["reason"]
    assert first.conflict_resolved is case["conflict_resolved"]

    assert all(
        decision == first
        for decision in observed_decisions
    )
