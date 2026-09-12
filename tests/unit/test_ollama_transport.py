import inspect
from typing import Any

import pytest

from villaz_router.ollama_execution.transport import (
    OllamaTransport,
)


class FakeOllamaTransport:
    def __init__(self) -> None:
        self.payloads: list[
            dict[str, object]
        ] = []
        self.closed = False
        self.response: object = {
            "model": "gemma3:12b",
            "message": {
                "role": "assistant",
                "content": "Generated response.",
            },
            "done": True,
        }

    async def chat(
        self,
        payload: dict[str, object],
    ) -> object:
        self.payloads.append(payload)
        return self.response

    async def aclose(self) -> None:
        self.closed = True


def test_transport_protocol_has_exact_async_contract() -> None:
    chat_signature = inspect.signature(
        OllamaTransport.chat
    )
    close_signature = inspect.signature(
        OllamaTransport.aclose
    )

    assert tuple(
        chat_signature.parameters
    ) == (
        "self",
        "payload",
    )
    assert (
        chat_signature.parameters[
            "payload"
        ].annotation
        == dict[str, object]
    )
    assert (
        chat_signature.return_annotation
        is object
    )
    assert inspect.iscoroutinefunction(
        OllamaTransport.chat
    )

    assert tuple(
        close_signature.parameters
    ) == ("self",)
    assert close_signature.return_annotation is None
    assert inspect.iscoroutinefunction(
        OllamaTransport.aclose
    )


def test_transport_protocol_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        OllamaTransport()


def test_structural_transport_implements_protocol() -> None:
    transport = FakeOllamaTransport()

    assert isinstance(
        transport,
        OllamaTransport,
    )


@pytest.mark.anyio
async def test_transport_chat_preserves_payload_identity() -> None:
    transport = FakeOllamaTransport()

    payload: dict[str, object] = {
        "model": "gemma3:12b",
        "messages": [
            {
                "role": "system",
                "content": "Canonical system prompt.",
            },
            {
                "role": "user",
                "content": "User prompt.",
            },
        ],
        "stream": False,
        "think": False,
    }

    result = await transport.chat(payload)

    assert result is transport.response
    assert transport.payloads == [payload]
    assert transport.payloads[0] is payload
    assert transport.closed is False


@pytest.mark.anyio
async def test_transport_aclose_is_async() -> None:
    transport = FakeOllamaTransport()

    result = await transport.aclose()

    assert result is None
    assert transport.closed is True


def test_protocol_module_has_no_httpx2_runtime_symbol() -> None:
    module_globals: dict[str, Any] = vars(
        __import__(
            "villaz_router.ollama_execution.transport",
            fromlist=["*"],
        )
    )

    assert "httpx2" not in module_globals
    assert "AsyncClient" not in module_globals
    assert "AsyncHTTPTransport" not in module_globals
