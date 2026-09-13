import json
from typing import NoReturn

import httpx2

from villaz_router.ollama_execution.errors import (
    OllamaTransportError,
    OllamaTransportErrorCode,
)

_MAX_PROVIDER_ERROR_MESSAGE_CHARS = 1024

def _raise_transport_error(
    code: OllamaTransportErrorCode,
    message: str,
    cause: BaseException | None = None,
    status_code: int | None = None,
    provider_error_message: str | None = None,
) -> NoReturn:
    error = OllamaTransportError(
        code=code,
        message=message,
        status_code=status_code,
        provider_error_message=provider_error_message,
        cause=cause,
    )

    if cause is None:
        raise error from None

    raise error from cause


def _extract_nested_provider_error_message(
    message: str,
) -> tuple[bool, str | None]:
    try:
        nested_body = json.loads(message)
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return False, None

    if not isinstance(nested_body, dict):
        return True, None

    if set(nested_body) != {"error"}:
        return True, None

    nested_error = nested_body.get("error")

    if not isinstance(nested_error, dict):
        return True, None

    value = nested_error.get("message")

    if not isinstance(value, str):
        return True, None

    nested_message = value.strip()

    if nested_message == "":
        return True, None

    if (
        len(nested_message)
        > _MAX_PROVIDER_ERROR_MESSAGE_CHARS
    ):
        return True, None

    return True, nested_message


def _extract_provider_error_message(
    response: httpx2.Response,
) -> str | None:
    try:
        body = response.json()
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        httpx2.DecodingError,
    ):
        return None

    if not isinstance(body, dict):
        return None

    if set(body) != {"error"}:
        return None

    value = body.get("error")

    if not isinstance(value, str):
        return None

    message = value.strip()

    if message == "":
        return None

    if len(message) > _MAX_PROVIDER_ERROR_MESSAGE_CHARS:
        return None

    is_nested_json, nested_message = (
        _extract_nested_provider_error_message(
            message
        )
    )

    if is_nested_json:
        return nested_message

    return message


class Httpx2OllamaTransport:
    def __init__(
        self,
        client: httpx2.AsyncClient,
    ) -> None:
        self._client = client

    async def chat(
        self,
        payload: dict[str, object],
    ) -> object:
        try:
            response = await self._client.post(
                "/api/chat",
                json=payload,
            )
        except httpx2.ConnectTimeout as exc:
            _raise_transport_error(
                OllamaTransportErrorCode
                .CONNECT_TIMEOUT,
                "unable to connect to ollama "
                "before timeout",
                exc,
            )
        except httpx2.ReadTimeout as exc:
            _raise_transport_error(
                OllamaTransportErrorCode.READ_TIMEOUT,
                "ollama response timed out",
                exc,
            )
        except httpx2.WriteTimeout as exc:
            _raise_transport_error(
                OllamaTransportErrorCode
                .WRITE_TIMEOUT,
                "ollama request write timed out",
                exc,
            )
        except httpx2.PoolTimeout as exc:
            _raise_transport_error(
                OllamaTransportErrorCode.POOL_TIMEOUT,
                "ollama connection pool timed out",
                exc,
            )
        except (
            httpx2.ProtocolError,
            httpx2.UnsupportedProtocol,
        ) as exc:
            _raise_transport_error(
                OllamaTransportErrorCode
                .PROTOCOL_ERROR,
                "ollama protocol failure",
                exc,
            )
        except (
            httpx2.ConnectError,
            httpx2.ReadError,
            httpx2.WriteError,
            httpx2.CloseError,
        ) as exc:
            _raise_transport_error(
                OllamaTransportErrorCode.NETWORK_ERROR,
                "ollama network request failed",
                exc,
            )

        if not 200 <= response.status_code < 300:
            _raise_transport_error(
                OllamaTransportErrorCode
                .HTTP_STATUS_ERROR,
                "ollama returned a non-success status",
                status_code=response.status_code,
                provider_error_message=(
                    _extract_provider_error_message(
                        response
                    )
                ),
            )

        try:
            return response.json()
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            httpx2.DecodingError,
        ) as exc:
            _raise_transport_error(
                OllamaTransportErrorCode
                .INVALID_JSON_RESPONSE,
                "ollama returned invalid JSON",
                exc,
                status_code=response.status_code,
            )

    async def aclose(self) -> None:
        await self._client.aclose()
