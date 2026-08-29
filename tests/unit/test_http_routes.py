from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.http_api.dependencies import (
    get_runtime_context,
)
from villaz_router.http_api.models import (
    LivenessResponse,
    ReadinessResponse,
)
from villaz_router.http_api.routes import router
from villaz_router.models import RulesetSnapshot
from villaz_router.registry_models import ProfileRegistrySnapshot


def make_runtime_context(root: Path) -> RuntimeContext:
    return RuntimeContext.model_construct(
        configuration_root=root,
        ruleset=RulesetSnapshot.model_construct(),
        profile_registry=(
            ProfileRegistrySnapshot.model_construct()
        ),
    )


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_router_has_exact_routes_and_methods() -> None:
    routes_by_path = {
        route.path: route
        for route in router.routes
    }

    assert set(routes_by_path) == {
        "/health/live",
        "/health/ready",
    }

    live_route = routes_by_path["/health/live"]
    ready_route = routes_by_path["/health/ready"]

    assert live_route.methods == {"GET"}
    assert ready_route.methods == {"GET"}
    assert live_route.response_model is LivenessResponse
    assert ready_route.response_model is ReadinessResponse


def test_liveness_returns_exact_response_without_context() -> None:
    app = make_app()
    app.state.runtime_context = "invalid"

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
    }


def test_readiness_returns_exact_response_with_context(
    tmp_path: Path,
) -> None:
    app = make_app()
    app.state.runtime_context = make_runtime_context(
        tmp_path.resolve()
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }


def test_readiness_uses_runtime_context_dependency(
    tmp_path: Path,
) -> None:
    app = make_app()
    context = make_runtime_context(tmp_path.resolve())
    calls = 0

    def override_runtime_context() -> RuntimeContext:
        nonlocal calls
        calls += 1
        return context

    app.dependency_overrides[get_runtime_context] = (
        override_runtime_context
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }
    assert calls == 1


def test_readiness_does_not_translate_missing_context() -> None:
    app = make_app()

    with TestClient(app) as client:
        with pytest.raises(
            RuntimeError,
            match=(
                "runtime context is unavailable outside "
                "the active application lifespan"
            ),
        ):
            client.get("/health/ready")


@pytest.mark.parametrize(
    "path",
    [
        "/health/live",
        "/health/ready",
    ],
)
def test_health_routes_reject_post(path: str) -> None:
    app = make_app()

    with TestClient(app) as client:
        response = client.post(path)

    assert response.status_code == 405
    assert response.json() == {
        "detail": "Method Not Allowed",
    }


def test_unknown_route_returns_not_found() -> None:
    app = make_app()

    with TestClient(app) as client:
        response = client.get("/unknown")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Not Found",
    }
