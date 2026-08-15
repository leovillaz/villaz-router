import json
from pathlib import Path


MATRIX_PATH = Path(__file__).with_name("router_v1_cases.json")
REQUIRED_FIELDS = {
    "id",
    "category",
    "message",
    "requested_profile",
    "expected_state",
    "expected_profile",
    "reason",
    "conflict_resolved",
    "rule",
    "repetitions",
    "expected_error",
}


def _matrix() -> dict[str, object]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_matrix_contains_rt_001_through_rt_048() -> None:
    cases = _matrix()["cases"]

    assert len(cases) == 48
    assert [case["id"] for case in cases] == [
        f"RT-{number:03d}"
        for number in range(1, 49)
    ]


def test_every_case_has_the_normative_contract_fields() -> None:
    for case in _matrix()["cases"]:
        assert set(case) == REQUIRED_FIELDS
        assert case["message"].strip()
        assert case["repetitions"] >= 1


def test_manual_and_invalid_profile_contracts_are_explicit() -> None:
    cases = _matrix()["cases"]

    for case in cases[:4]:
        assert case["expected_state"] == "explicit"
        assert case["reason"] == "user_selected_profile"
        assert case["conflict_resolved"] is False

    for case in cases[36:40]:
        assert case["expected_state"] == "error"
        assert case["expected_error"] == "INVALID_PROFILE"
        assert case["expected_profile"] is None


def test_determinism_cases_require_ten_repetitions() -> None:
    cases = _matrix()["cases"]

    assert [case["id"] for case in cases[-4:]] == [
        "RT-045",
        "RT-046",
        "RT-047",
        "RT-048",
    ]
    assert all(case["repetitions"] == 10 for case in cases[-4:])
