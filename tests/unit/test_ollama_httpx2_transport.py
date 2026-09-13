import json
from collections.abc import Callable
from typing import Any

import httpx2
import pytest

from villaz_router.ollama_execution.errors import (
    OllamaTransportError,
    OllamaTransportErrorCode,
)
from villaz_router.ollama_execution.httpx2_transport import (
    Httpx2OllamaTransport,
)
from villaz_router.ollama_execution.transport import (
    OllamaTransport,
)


Handler = Callable[
    [httpx2.Request],
    httpx2.Response,
]


def make_client(
    handler: Handler,
) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        base_url="http://127.0.0.1:11434",
        transport=httpx2.MockTransport(handler),
        follow_redirects=False,
        trust_env=False,
    )


def make_payload() -> dict[str, object]:
    return {
        "model": "gemma3:12b",
        "messages": [
            {
                "role": "system",
                "content": "SENSITIVE_SYSTEM_PROMPT",
            },
            {
                "role": "user",
                "content": "SENSITIVE_USER_PROMPT",
            },
        ],
        "stream": False,
        "think": False,
    }


def test_httpx2_transport_implements_protocol() -> None:
    client = make_client(
        lambda request: httpx2.Response(
            200,
            json={},
        )
    )
    transport = Httpx2OllamaTransport(client)

    assert isinstance(
        transport,
        OllamaTransport,
    )


@pytest.mark.anyio
async def test_chat_uses_exact_endpoint_and_payload() -> None:
    requests: list[httpx2.Request] = []

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        requests.append(request)

        return httpx2.Response(
            200,
            json={
                "model": "gemma3:12b",
                "message": {
                    "role": "assistant",
                    "content": "Generated response.",
                },
                "done": True,
                "total_duration": 123,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)
    payload = make_payload()

    try:
        result = await transport.chat(payload)
    finally:
        await transport.aclose()

    assert len(requests) == 1

    request = requests[0]

    assert request.method == "POST"
    assert str(request.url) == (
        "http://127.0.0.1:11434/api/chat"
    )
    assert request.headers["content-type"] == (
        "application/json"
    )
    assert "authorization" not in request.headers
    assert "cookie" not in request.headers
    assert json.loads(request.content) == payload

    assert result == {
        "model": "gemma3:12b",
        "message": {
            "role": "assistant",
            "content": "Generated response.",
        },
        "done": True,
        "total_duration": 123,
    }


@pytest.mark.parametrize(
    (
        "exception_type",
        "expected_code",
    ),
    [
        (
            httpx2.ConnectTimeout,
            OllamaTransportErrorCode
            .CONNECT_TIMEOUT,
        ),
        (
            httpx2.ReadTimeout,
            OllamaTransportErrorCode.READ_TIMEOUT,
        ),
        (
            httpx2.WriteTimeout,
            OllamaTransportErrorCode
            .WRITE_TIMEOUT,
        ),
        (
            httpx2.PoolTimeout,
            OllamaTransportErrorCode.POOL_TIMEOUT,
        ),
        (
            httpx2.ConnectError,
            OllamaTransportErrorCode.NETWORK_ERROR,
        ),
        (
            httpx2.ReadError,
            OllamaTransportErrorCode.NETWORK_ERROR,
        ),
        (
            httpx2.WriteError,
            OllamaTransportErrorCode.NETWORK_ERROR,
        ),
        (
            httpx2.CloseError,
            OllamaTransportErrorCode.NETWORK_ERROR,
        ),
        (
            httpx2.ProtocolError,
            OllamaTransportErrorCode.PROTOCOL_ERROR,
        ),
        (
            httpx2.RemoteProtocolError,
            OllamaTransportErrorCode.PROTOCOL_ERROR,
        ),
        (
            httpx2.UnsupportedProtocol,
            OllamaTransportErrorCode.PROTOCOL_ERROR,
        ),
    ],
)
@pytest.mark.anyio
async def test_chat_translates_expected_httpx2_errors(
    exception_type: type[httpx2.HTTPError],
    expected_code: OllamaTransportErrorCode,
) -> None:
    requests: list[httpx2.Request] = []
    raised_errors: list[httpx2.HTTPError] = []

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        requests.append(request)

        error = exception_type(
            "SENSITIVE_HTTPX2_FAILURE",
            request=request,
        )
        raised_errors.append(error)
        raise error

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert len(requests) == 1
    assert len(raised_errors) == 1
    assert error.code is expected_code
    assert error.status_code is None
    assert error.cause is raised_errors[0]
    assert error.__cause__ is raised_errors[0]

    serialized = str(error) + repr(error)

    assert (
        "SENSITIVE_HTTPX2_FAILURE"
        not in serialized
    )
    assert (
        "SENSITIVE_SYSTEM_PROMPT"
        not in serialized
    )
    assert (
        "SENSITIVE_USER_PROMPT"
        not in serialized
    )


@pytest.mark.parametrize(
    "status_code",
    [
        307,
        400,
        404,
        500,
        503,
    ],
)
@pytest.mark.anyio
async def test_chat_rejects_non_success_status(
    status_code: int,
) -> None:
    calls = 0

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        nonlocal calls
        calls += 1

        return httpx2.Response(
            status_code,
            text="SENSITIVE_PROVIDER_ERROR_BODY",
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert calls == 1
    assert error.code is (
        OllamaTransportErrorCode
        .HTTP_STATUS_ERROR
    )
    assert error.status_code == status_code
    assert error.provider_error_message is None
    assert error.cause is None
    assert error.__cause__ is None

    serialized = str(error) + repr(error)

    assert (
        "SENSITIVE_PROVIDER_ERROR_BODY"
        not in serialized
    )
    assert (
        "SENSITIVE_USER_PROMPT"
        not in serialized
    )


@pytest.mark.parametrize(
    "status_code",
    [
        400,
        500,
    ],
)
@pytest.mark.anyio
async def test_chat_preserves_valid_provider_error_message(
    status_code: int,
) -> None:
    provider_message = (
        "request (300 tokens) exceeds the available "
        "context size (256 tokens)"
    )

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            status_code,
            json={
                "error": provider_message,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert error.code is (
        OllamaTransportErrorCode.HTTP_STATUS_ERROR
    )
    assert error.status_code == status_code
    assert error.provider_error_message == (
        provider_message
    )
    assert error.cause is None
    assert error.__cause__ is None

    serialized = str(error) + repr(error)

    assert provider_message not in serialized
    assert "SENSITIVE_SYSTEM_PROMPT" not in serialized
    assert "SENSITIVE_USER_PROMPT" not in serialized


@pytest.mark.anyio
async def test_chat_extracts_nested_ollama_context_error_message(
) -> None:
    provider_message = (
        "request (200030 tokens) exceeds the available "
        "context size (4096 tokens), try increasing it"
    )
    nested_provider_body = {
        "error": {
            "code": 400,
            "message": provider_message,
            "type": "exceed_context_size_error",
            "n_prompt_tokens": 200030,
            "n_ctx": 4096,
        }
    }

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            400,
            json={
                "error": json.dumps(
                    nested_provider_body,
                    separators=(",", ":"),
                ),
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert error.code is (
        OllamaTransportErrorCode.HTTP_STATUS_ERROR
    )
    assert error.status_code == 400
    assert error.provider_error_message == (
        provider_message
    )
    assert error.cause is None
    assert error.__cause__ is None

    assert (
        "exceed_context_size_error"
        not in error.provider_error_message
    )

    serialized = str(error) + repr(error)

    assert provider_message not in serialized
    assert "exceed_context_size_error" not in serialized
    assert "SENSITIVE_SYSTEM_PROMPT" not in serialized
    assert "SENSITIVE_USER_PROMPT" not in serialized


@pytest.mark.parametrize(
    "body",
    [
        {},
        {
            "error": 123,
        },
        {
            "error": "",
        },
        {
            "error": "   ",
        },
        {
            "error": "valid",
            "extra": "unexpected",
        },
        [
            "error",
        ],
    ],
)
@pytest.mark.anyio
async def test_chat_discards_invalid_provider_error_evidence(
    body: object,
) -> None:
    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            400,
            json=body,
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert error.code is (
        OllamaTransportErrorCode.HTTP_STATUS_ERROR
    )
    assert error.status_code == 400
    assert error.provider_error_message is None
    assert error.cause is None
    assert error.__cause__ is None


@pytest.mark.parametrize(
    "nested_value",
    [
        "{}",
        "[]",
        '"text"',
        '{"unexpected":"value"}',
        '{"error":"not-an-object"}',
        '{"error":{"message":123}}',
        '{"error":{"message":""}}',
    ],
)
@pytest.mark.anyio
async def test_chat_discards_unrecognized_nested_json_error(
    nested_value: str,
) -> None:
    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            400,
            json={
                "error": nested_value,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert error.code is (
        OllamaTransportErrorCode.HTTP_STATUS_ERROR
    )
    assert error.provider_error_message is None
    assert nested_value not in (
        str(error) + repr(error)
    )


@pytest.mark.anyio
async def test_chat_accepts_provider_error_message_at_limit() -> None:
    provider_message = "x" * 1024

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            400,
            json={
                "error": provider_message,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    assert (
        exc_info.value.provider_error_message
        == provider_message
    )


@pytest.mark.anyio
async def test_chat_discards_oversized_provider_error_message() -> None:
    provider_message = "x" * 1025

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            400,
            json={
                "error": provider_message,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert error.provider_error_message is None

    serialized = str(error) + repr(error)

    assert provider_message not in serialized


@pytest.mark.parametrize(
    ("content", "content_type"),
    [
        (
            b"not-json",
            "text/plain",
        ),
        (
            b'{"incomplete":',
            "application/json",
        ),
        (
            b"\xff\xfe",
            "application/json",
        ),
    ],
)
@pytest.mark.anyio
async def test_chat_rejects_invalid_json(
    content: bytes,
    content_type: str,
) -> None:
    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            200,
            content=content,
            headers={
                "content-type": content_type,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            OllamaTransportError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    error = exc_info.value

    assert error.code is (
        OllamaTransportErrorCode
        .INVALID_JSON_RESPONSE
    )
    assert error.status_code == 200
    assert isinstance(
        error.cause,
        (
            json.JSONDecodeError,
            UnicodeDecodeError,
            httpx2.DecodingError,
        ),
    )
    assert error.__cause__ is error.cause


@pytest.mark.anyio
async def test_chat_returns_any_valid_json_value() -> None:
    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        return httpx2.Response(
            200,
            json=[
                "valid",
                "json",
            ],
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        result = await transport.chat(
            make_payload()
        )
    finally:
        await transport.aclose()

    assert result == [
        "valid",
        "json",
    ]


@pytest.mark.anyio
async def test_unexpected_error_is_not_masked() -> None:
    expected = RuntimeError(
        "unexpected transport failure"
    )

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        raise expected

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)

    try:
        with pytest.raises(
            RuntimeError
        ) as exc_info:
            await transport.chat(
                make_payload()
            )
    finally:
        await transport.aclose()

    assert exc_info.value is expected


@pytest.mark.anyio
async def test_aclose_closes_owned_client() -> None:
    client = make_client(
        lambda request: httpx2.Response(
            200,
            json={},
        )
    )
    transport = Httpx2OllamaTransport(client)

    assert client.is_closed is False

    result = await transport.aclose()

    assert result is None
    assert client.is_closed is True
