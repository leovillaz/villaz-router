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
        "system": "SENSITIVE_SYSTEM_PROMPT",
        "prompt": "SENSITIVE_USER_PROMPT",
        "stream": False,
        "raw": False,
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
async def test_generate_uses_exact_endpoint_and_payload() -> None:
    requests: list[httpx2.Request] = []

    def handler(
        request: httpx2.Request,
    ) -> httpx2.Response:
        requests.append(request)

        return httpx2.Response(
            200,
            json={
                "model": "gemma3:12b",
                "response": "Generated response.",
                "done": True,
                "total_duration": 123,
            },
        )

    client = make_client(handler)
    transport = Httpx2OllamaTransport(client)
    payload = make_payload()

    try:
        result = await transport.generate(payload)
    finally:
        await transport.aclose()

    assert len(requests) == 1

    request = requests[0]

    assert request.method == "POST"
    assert str(request.url) == (
        "http://127.0.0.1:11434/api/generate"
    )
    assert request.headers["content-type"] == (
        "application/json"
    )
    assert "authorization" not in request.headers
    assert "cookie" not in request.headers
    assert json.loads(request.content) == payload

    assert result == {
        "model": "gemma3:12b",
        "response": "Generated response.",
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
async def test_generate_translates_expected_httpx2_errors(
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
            await transport.generate(make_payload())
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
async def test_generate_rejects_non_success_status(
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
            await transport.generate(make_payload())
    finally:
        await transport.aclose()

    error = exc_info.value

    assert calls == 1
    assert error.code is (
        OllamaTransportErrorCode
        .HTTP_STATUS_ERROR
    )
    assert error.status_code == status_code
    assert isinstance(
        error.cause,
        httpx2.HTTPStatusError,
    )
    assert error.__cause__ is error.cause

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
async def test_generate_rejects_invalid_json(
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
            await transport.generate(make_payload())
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
async def test_generate_returns_any_valid_json_value() -> None:
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
        result = await transport.generate(
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
            await transport.generate(make_payload())
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
