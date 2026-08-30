import json
from typing import NoReturn

import httpx2

from villaz_router.ollama_execution.errors import (
    OllamaTransportError,
    OllamaTransportErrorCode,
)


def _raise_transport_error(
    code: OllamaTransportErrorCode,
    message: str,
    cause: BaseException,
    status_code: int | None = None,
) -> NoReturn:
    raise OllamaTransportError(
        code=code,
        message=message,
        status_code=status_code,
        cause=cause,
    ) from cause


class Httpx2OllamaTransport:
    def __init__(
        self,
        client: httpx2.AsyncClient,
    ) -> None:
        self._client = client

    async def generate(
        self,
        payload: dict[str, object],
    ) -> object:
        try:
            response = await self._client.post(
                "/api/generate",
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

        try:
            response.raise_for_status()
        except httpx2.HTTPStatusError as exc:
            _raise_transport_error(
                OllamaTransportErrorCode
                .HTTP_STATUS_ERROR,
                "ollama returned a non-success status",
                exc,
                status_code=response.status_code,
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
