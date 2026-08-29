from typing import Any

import pytest
from pydantic import ValidationError

from villaz_router.http_api.models import (
    LivenessResponse,
    ReadinessResponse,
)


@pytest.mark.parametrize(
    "model_type",
    [
        LivenessResponse,
        ReadinessResponse,
    ],
)
def test_health_response_has_exact_fields(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
) -> None:
    assert set(model_type.model_fields) == {"status"}
    assert model_type.model_config["extra"] == "forbid"
    assert model_type.model_config["frozen"] is True


def test_liveness_response_has_exact_payload() -> None:
    response = LivenessResponse()

    assert response.status == "alive"
    assert response.model_dump(mode="json") == {
        "status": "alive",
    }


def test_readiness_response_has_exact_payload() -> None:
    response = ReadinessResponse()

    assert response.status == "ready"
    assert response.model_dump(mode="json") == {
        "status": "ready",
    }


@pytest.mark.parametrize(
    ("model_type", "status"),
    [
        (LivenessResponse, "alive"),
        (ReadinessResponse, "ready"),
    ],
)
def test_health_response_is_frozen(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
    status: str,
) -> None:
    response = model_type.model_validate({"status": status})

    with pytest.raises(ValidationError):
        response.status = "changed"


@pytest.mark.parametrize(
    ("model_type", "status"),
    [
        (LivenessResponse, "alive"),
        (ReadinessResponse, "ready"),
    ],
)
def test_health_response_forbids_extra_fields(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
    status: str,
) -> None:
    with pytest.raises(ValidationError):
        model_type.model_validate({
            "status": status,
            "unexpected": True,
        })


@pytest.mark.parametrize(
    ("model_type", "invalid_status"),
    [
        (LivenessResponse, "ready"),
        (ReadinessResponse, "alive"),
        (LivenessResponse, 1),
        (ReadinessResponse, None),
    ],
)
def test_health_response_rejects_invalid_status(
    model_type: type[LivenessResponse] | type[ReadinessResponse],
    invalid_status: Any,
) -> None:
    with pytest.raises(ValidationError):
        model_type.model_validate({
            "status": invalid_status,
        })
