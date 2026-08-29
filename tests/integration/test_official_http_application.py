from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.http_api import create_app


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_REGISTRY_HASH = (
    "c9b7ef321815b11f6a38fcd0c4b3538b"
    "c549e78a41a1149760e3c49f8dcbf6af"
)


def assert_runtime_context_absent(application: object) -> None:
    with pytest.raises(AttributeError):
        application.state.runtime_context


def test_official_http_application_is_ready() -> None:
    application = create_app(ROOT)
    assert_runtime_context_absent(application)

    with TestClient(application) as client:
        context = application.state.runtime_context

        assert isinstance(context, RuntimeContext)
        assert context.configuration_root == ROOT
        assert len(context.ruleset.ruleset_hash) == 64
        int(context.ruleset.ruleset_hash, 16)

        registry = context.profile_registry

        assert (
            registry.registry_hash
            == EXPECTED_REGISTRY_HASH
        )
        assert len(registry.profiles) == 5
        assert all(
            profile.enabled
            for profile in registry.profiles
        )

        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")

        assert live_response.status_code == 200
        assert live_response.json() == {
            "status": "alive",
        }
        assert ready_response.status_code == 200
        assert ready_response.json() == {
            "status": "ready",
        }

    assert_runtime_context_absent(application)


def test_official_health_responses_expose_no_runtime_data() -> None:
    application = create_app(ROOT)

    with TestClient(application) as client:
        payloads = (
            client.get("/health/live").json(),
            client.get("/health/ready").json(),
        )

    assert payloads == (
        {"status": "alive"},
        {"status": "ready"},
    )

    serialized = repr(payloads)

    assert EXPECTED_REGISTRY_HASH not in serialized
    assert str(ROOT) not in serialized
    assert "system_prompt" not in serialized
    assert "model" not in serialized
