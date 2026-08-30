import inspect
from typing import Any

import pytest

import villaz_router.ollama_execution.factory as factory_module
from villaz_router.ollama_execution.config import (
    OllamaClientConfig,
    OllamaConnectionLimits,
    OllamaTimeoutConfig,
)
from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)
from villaz_router.ollama_execution.factory import (
    create_ollama_executor,
)


def make_config(
    base_url: str = (
        "http://127.0.0.1:11434"
    ),
) -> OllamaClientConfig:
    return OllamaClientConfig(
        base_url=base_url,
        timeouts=OllamaTimeoutConfig(
            connect_seconds=5.0,
            read_seconds=300.0,
            write_seconds=10.0,
            pool_seconds=5.0,
        ),
        limits=OllamaConnectionLimits(
            max_connections=1,
            max_keepalive_connections=1,
            keepalive_expiry_seconds=30.0,
        ),
    )


def test_factory_has_exact_sync_contract() -> None:
    signature = inspect.signature(
        create_ollama_executor
    )

    assert tuple(signature.parameters) == (
        "config",
    )
    assert (
        signature.parameters[
            "config"
        ].annotation
        is OllamaClientConfig
    )
    assert (
        signature.parameters["config"].default
        is inspect.Parameter.empty
    )
    assert signature.return_annotation is (
        OllamaExecutor
    )
    assert not inspect.iscoroutinefunction(
        create_ollama_executor
    )


def test_factory_composes_exact_httpx2_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_order: list[str] = []
    records: dict[str, dict[str, Any]] = {}

    timeout_object = object()
    limits_object = object()
    http_transport_object = object()
    client_object = object()
    ollama_transport_object = object()
    executor_object = object()

    def fake_timeout(
        **kwargs: Any,
    ) -> object:
        call_order.append("timeout")
        records["timeout"] = kwargs
        return timeout_object

    def fake_limits(
        **kwargs: Any,
    ) -> object:
        call_order.append("limits")
        records["limits"] = kwargs
        return limits_object

    def fake_http_transport(
        **kwargs: Any,
    ) -> object:
        call_order.append("http_transport")
        records["http_transport"] = kwargs
        return http_transport_object

    def fake_client(
        **kwargs: Any,
    ) -> object:
        call_order.append("client")
        records["client"] = kwargs
        return client_object

    def fake_ollama_transport(
        client: object,
    ) -> object:
        call_order.append("ollama_transport")
        records["ollama_transport"] = {
            "client": client,
        }
        return ollama_transport_object

    def fake_executor(
        transport: object,
    ) -> object:
        call_order.append("executor")
        records["executor"] = {
            "transport": transport,
        }
        return executor_object

    monkeypatch.setattr(
        factory_module.httpx2,
        "Timeout",
        fake_timeout,
    )
    monkeypatch.setattr(
        factory_module.httpx2,
        "Limits",
        fake_limits,
    )
    monkeypatch.setattr(
        factory_module.httpx2,
        "AsyncHTTPTransport",
        fake_http_transport,
    )
    monkeypatch.setattr(
        factory_module.httpx2,
        "AsyncClient",
        fake_client,
    )
    monkeypatch.setattr(
        factory_module,
        "Httpx2OllamaTransport",
        fake_ollama_transport,
    )
    monkeypatch.setattr(
        factory_module,
        "OllamaExecutor",
        fake_executor,
    )

    result = create_ollama_executor(
        make_config()
    )

    assert result is executor_object
    assert call_order == [
        "timeout",
        "limits",
        "http_transport",
        "client",
        "ollama_transport",
        "executor",
    ]

    assert records["timeout"] == {
        "connect": 5.0,
        "read": 300.0,
        "write": 10.0,
        "pool": 5.0,
    }
    assert records["limits"] == {
        "max_connections": 1,
        "max_keepalive_connections": 1,
        "keepalive_expiry": 30.0,
    }
    assert records["http_transport"] == {
        "trust_env": False,
        "http1": True,
        "http2": False,
        "limits": limits_object,
        "retries": 0,
    }
    assert records["client"] == {
        "base_url": (
            "http://127.0.0.1:11434"
        ),
        "timeout": timeout_object,
        "follow_redirects": False,
        "limits": limits_object,
        "transport": http_transport_object,
        "trust_env": False,
        "http1": True,
        "http2": False,
    }
    assert records["ollama_transport"] == {
        "client": client_object,
    }
    assert records["executor"] == {
        "transport": ollama_transport_object,
    }


def test_factory_normalizes_only_root_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_base_urls: list[str] = []

    class FakeClient:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            captured_base_urls.append(
                kwargs["base_url"]
            )

    monkeypatch.setattr(
        factory_module.httpx2,
        "Timeout",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        factory_module.httpx2,
        "Limits",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        factory_module.httpx2,
        "AsyncHTTPTransport",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        factory_module.httpx2,
        "AsyncClient",
        FakeClient,
    )
    monkeypatch.setattr(
        factory_module,
        "Httpx2OllamaTransport",
        lambda client: object(),
    )
    monkeypatch.setattr(
        factory_module,
        "OllamaExecutor",
        lambda transport: object(),
    )

    create_ollama_executor(
        make_config(
            "http://127.0.0.1:11434/"
        )
    )

    assert captured_base_urls == [
        "http://127.0.0.1:11434",
    ]


@pytest.mark.anyio
async def test_factory_creates_real_executor_without_network() -> None:
    executor = create_ollama_executor(
        make_config()
    )

    try:
        assert isinstance(
            executor,
            OllamaExecutor,
        )
    finally:
        await executor.aclose()


@pytest.mark.anyio
async def test_factory_does_not_create_singleton() -> None:
    first = create_ollama_executor(
        make_config()
    )
    second = create_ollama_executor(
        make_config()
    )

    try:
        assert first is not second
    finally:
        await first.aclose()
        await second.aclose()


@pytest.mark.anyio
async def test_factory_supports_https_without_preflight() -> None:
    executor = create_ollama_executor(
        make_config(
            "https://ollama.internal:11434"
        )
    )

    try:
        assert isinstance(
            executor,
            OllamaExecutor,
        )
    finally:
        await executor.aclose()
