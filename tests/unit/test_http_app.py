import inspect
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import villaz_router.http_api.app as http_app
from villaz_router.bootstrap_errors import (
    ApplicationBootstrapError,
    ApplicationBootstrapErrorCode,
    BootstrapStage,
)
from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.http_api.app import create_app
from villaz_router.models import RulesetSnapshot
from villaz_router.ollama_execution.config import (
    OllamaClientConfig,
)
from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)
from villaz_router.registry_models import (
    ProfileRegistrySnapshot,
)


def make_runtime_context(
    root: Path,
) -> RuntimeContext:
    return RuntimeContext.model_construct(
        configuration_root=root,
        ruleset=RulesetSnapshot.model_construct(),
        profile_registry=(
            ProfileRegistrySnapshot.model_construct()
        ),
    )


def make_ollama_config() -> OllamaClientConfig:
    return OllamaClientConfig.model_construct()


class FakeOllamaTransport:
    async def generate(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        raise AssertionError(
            "network execution must not occur"
        )

    async def aclose(self) -> None:
        return None


def make_ollama_executor() -> OllamaExecutor:
    return OllamaExecutor(
        FakeOllamaTransport()
    )


def patch_ollama_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> OllamaExecutor:
    config = make_ollama_config()
    executor = make_ollama_executor()

    monkeypatch.setattr(
        http_app,
        "load_ollama_client_config",
        lambda configuration_root: config,
    )
    monkeypatch.setattr(
        http_app,
        "create_ollama_executor",
        lambda received_config: executor,
    )

    return executor


def assert_runtime_context_absent(
    app: FastAPI,
) -> None:
    with pytest.raises(AttributeError):
        app.state.runtime_context

def assert_ollama_executor_absent(
    app: FastAPI,
) -> None:
    with pytest.raises(AttributeError):
        app.state.ollama_executor

def test_create_app_has_exact_sync_contract_and_is_pure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        pytest.fail(
            "bootstrap must not run during app creation"
        )

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fail_if_called,
    )

    signature = inspect.signature(create_app)
    application = create_app(None)

    assert tuple(signature.parameters) == (
        "configuration_root",
    )
    assert (
        signature.parameters[
            "configuration_root"
        ].default
        is inspect.Parameter.empty
    )
    assert signature.return_annotation is FastAPI
    assert not inspect.iscoroutinefunction(
        create_app
    )
    assert isinstance(application, FastAPI)
    assert_runtime_context_absent(application)


def test_lifespan_bootstraps_once_and_publishes_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    context = make_runtime_context(root)
    calls: list[str | Path | None] = []

    def fake_bootstrap(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        calls.append(configuration_root)
        return context

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fake_bootstrap,
    )

    executor = patch_ollama_startup(
        monkeypatch
    )

    application = create_app(root)
    assert_runtime_context_absent(application)

    with TestClient(application) as client:
        assert (
            application.state.runtime_context
            is context
        )
        assert (
            application.state.ollama_executor
            is executor
        )

        assert client.get(
            "/health/live"
        ).json() == {
            "status": "alive",
        }
        assert client.get(
            "/health/ready"
        ).json() == {
            "status": "ready",
        }

    assert calls == [root]
    assert_runtime_context_absent(application)


def test_lifespan_cleanup_runs_when_body_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_runtime_context(
        tmp_path.resolve()
    )

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        lambda configuration_root: context,
    )

    executor = patch_ollama_startup(
        monkeypatch
    )

    application = create_app(tmp_path)

    with pytest.raises(
        RuntimeError,
        match="test body failed",
    ):
        with TestClient(application):
            assert (
                application.state.runtime_context
                is context
            )
            assert (
                application.state.ollama_executor
                is executor
            )

            raise RuntimeError(
                "test body failed"
            )

    assert_runtime_context_absent(application)


def test_bootstrap_error_propagates_and_prevents_startup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected_error = ApplicationBootstrapError(
        code=(
            ApplicationBootstrapErrorCode
            .ROOT_NOT_FOUND
        ),
        stage=BootstrapStage.CONFIGURATION_ROOT,
        message="configuration root not found",
    )

    def fail_bootstrap(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        raise expected_error

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fail_bootstrap,
    )

    application = create_app(tmp_path)

    with pytest.raises(
        ApplicationBootstrapError,
    ) as exc_info:
        with TestClient(application):
            pytest.fail(
                "startup must not complete"
            )

    assert exc_info.value is expected_error
    assert_runtime_context_absent(application)


def test_unexpected_bootstrap_error_is_not_masked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected_error = RuntimeError(
        "unexpected bootstrap failure"
    )

    def fail_bootstrap(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        raise expected_error

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fail_bootstrap,
    )

    application = create_app(tmp_path)

    with pytest.raises(
        RuntimeError,
    ) as exc_info:
        with TestClient(application):
            pytest.fail(
                "startup must not complete"
            )

    assert exc_info.value is expected_error
    assert_runtime_context_absent(application)


def test_each_lifespan_cycle_bootstraps_again(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first = make_runtime_context(
        (tmp_path / "first").resolve()
    )
    second = make_runtime_context(
        (tmp_path / "second").resolve()
    )
    contexts = iter((first, second))
    calls: list[str | Path | None] = []

    def fake_bootstrap(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        calls.append(configuration_root)
        return next(contexts)

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fake_bootstrap,
    )

    patch_ollama_startup(monkeypatch)

    application = create_app(tmp_path)

    with TestClient(application):
        assert (
            application.state.runtime_context
            is first
        )

    assert_runtime_context_absent(application)

    with TestClient(application):
        assert (
            application.state.runtime_context
            is second
        )

    assert_runtime_context_absent(application)

    assert calls == [
        tmp_path,
        tmp_path,
    ]


def test_applications_have_independent_runtime_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first_root = (
        tmp_path / "first"
    ).resolve()
    second_root = (
        tmp_path / "second"
    ).resolve()

    contexts = {
        first_root: make_runtime_context(
            first_root
        ),
        second_root: make_runtime_context(
            second_root
        ),
    }

    def fake_bootstrap(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        return contexts[configuration_root]

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fake_bootstrap,
    )

    patch_ollama_startup(monkeypatch)

    first_app = create_app(first_root)
    second_app = create_app(second_root)

    assert first_app is not second_app

    with TestClient(first_app):
        assert (
            first_app.state.runtime_context
            is contexts[first_root]
        )
        assert_runtime_context_absent(
            second_app
        )

        with TestClient(second_app):
            assert (
                second_app.state.runtime_context
                is contexts[second_root]
            )
            assert (
                first_app.state.runtime_context
                is contexts[first_root]
            )

        assert_runtime_context_absent(
            second_app
        )

    assert_runtime_context_absent(
        first_app
    )


def test_documentation_endpoints_are_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_runtime_context(
        tmp_path.resolve()
    )

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        lambda configuration_root: context,
    )

    patch_ollama_startup(monkeypatch)

    application = create_app(tmp_path)

    with TestClient(application) as client:
        responses = {
            path: client.get(path)
            for path in (
                "/docs",
                "/redoc",
                "/openapi.json",
            )
        }

    assert {
        path: response.status_code
        for path, response in responses.items()
    } == {
        "/docs": 404,
        "/redoc": 404,
        "/openapi.json": 404,
    }

    assert all(
        response.json()
        == {"detail": "Not Found"}
        for response in responses.values()
    )


def test_lifespan_composes_ollama_startup_in_exact_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    context = make_runtime_context(root)
    config = make_ollama_config()
    executor = make_ollama_executor()

    calls: list[
        tuple[str, object]
    ] = []

    def fake_bootstrap(
        configuration_root: str | Path | None,
    ) -> RuntimeContext:
        calls.append(
            (
                "bootstrap",
                configuration_root,
            )
        )
        return context

    def fake_load_config(
        configuration_root: Path,
    ) -> OllamaClientConfig:
        calls.append(
            (
                "load_config",
                configuration_root,
            )
        )
        return config

    def fake_create_executor(
        received_config: OllamaClientConfig,
    ) -> OllamaExecutor:
        calls.append(
            (
                "create_executor",
                received_config,
            )
        )
        return executor

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        fake_bootstrap,
    )
    monkeypatch.setattr(
        http_app,
        "load_ollama_client_config",
        fake_load_config,
    )
    monkeypatch.setattr(
        http_app,
        "create_ollama_executor",
        fake_create_executor,
    )

    application = create_app(root)

    with TestClient(application):
        assert (
            application.state.runtime_context
            is context
        )
        assert (
            application.state.ollama_executor
            is executor
        )

    assert calls == [
        (
            "bootstrap",
            root,
        ),
        (
            "load_config",
            root,
        ),
        (
            "create_executor",
            config,
        ),
    ]

def test_lifespan_closes_executor_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_runtime_context(
        tmp_path.resolve()
    )
    executor = make_ollama_executor()
    calls: list[str] = []

    async def fake_aclose() -> None:
        calls.append("aclose")

    executor.aclose = fake_aclose

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        lambda configuration_root: context,
    )
    monkeypatch.setattr(
        http_app,
        "load_ollama_client_config",
        lambda configuration_root: (
            make_ollama_config()
        ),
    )
    monkeypatch.setattr(
        http_app,
        "create_ollama_executor",
        lambda config: executor,
    )

    application = create_app(tmp_path)

    with TestClient(application):
        assert (
            application.state.ollama_executor
            is executor
        )

    assert calls == ["aclose"]
    assert_runtime_context_absent(application)
    assert_ollama_executor_absent(application)


def test_lifespan_cleanup_runs_when_executor_close_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_runtime_context(
        tmp_path.resolve()
    )
    executor = make_ollama_executor()
    expected_error = RuntimeError(
        "executor close failed"
    )

    async def fail_aclose() -> None:
        raise expected_error

    executor.aclose = fail_aclose

    monkeypatch.setattr(
        http_app,
        "bootstrap_runtime",
        lambda configuration_root: context,
    )
    monkeypatch.setattr(
        http_app,
        "load_ollama_client_config",
        lambda configuration_root: (
            make_ollama_config()
        ),
    )
    monkeypatch.setattr(
        http_app,
        "create_ollama_executor",
        lambda config: executor,
    )

    application = create_app(tmp_path)

    with pytest.raises(RuntimeError) as exc_info:
        with TestClient(application):
            assert (
                application.state.runtime_context
                is context
            )
            assert (
                application.state.ollama_executor
                is executor
            )

    assert exc_info.value is expected_error
    assert_runtime_context_absent(application)
    assert_ollama_executor_absent(application)
