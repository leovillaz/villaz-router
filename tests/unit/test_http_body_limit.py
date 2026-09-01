import ast
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.types import (
    Message,
    Receive,
    Scope,
    Send,
)

import villaz_router.http_api.body_limit as body_limit
from villaz_router.http_api.body_limit import (
    MAX_REQUEST_BODY_BYTES,
    RequestBodyLimitMiddleware,
)
from villaz_router.http_api.models import PromptRequest


def make_http_scope(
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/probe",
        "raw_path": b"/probe",
        "query_string": b"",
        "root_path": "",
        "headers": headers or [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }


def run_http_middleware(
    request_messages: list[Message],
    *,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> tuple[int, list[Message], list[Message]]:
    downstream_calls = 0
    downstream_messages: list[Message] = []
    sent_messages: list[Message] = []

    async def exercise() -> None:
        messages = iter(request_messages)

        async def receive() -> Message:
            try:
                return next(messages)
            except StopIteration as exc:
                raise AssertionError(
                    "receive called after request completion"
                ) from exc

        async def send(message: Message) -> None:
            sent_messages.append(message)

        async def downstream(
            scope: Scope,
            receive: Receive,
            send: Send,
        ) -> None:
            nonlocal downstream_calls
            downstream_calls += 1

            while True:
                message = await receive()
                downstream_messages.append(message)

                if message["type"] == "http.disconnect":
                    break
                if not message.get("more_body", False):
                    break

            await send({
                "type": "http.response.start",
                "status": 204,
                "headers": [],
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })

        middleware = RequestBodyLimitMiddleware(
            downstream
        )
        await middleware(
            make_http_scope(headers),
            receive,
            send,
        )

    asyncio.run(exercise())
    return (
        downstream_calls,
        downstream_messages,
        sent_messages,
    )


def response_status(messages: list[Message]) -> int:
    start = next(
        message
        for message in messages
        if message["type"] == "http.response.start"
    )
    return start["status"]


def response_payload(messages: list[Message]) -> object:
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return json.loads(body)


def test_body_limit_has_no_pydantic_model_dependency() -> None:
    path = Path(body_limit.__file__)
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(
                alias.name
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            module = node.module or ""
            imported_module = f"{prefix}{module}"
            imported_modules.add(imported_module)
            separator = (
                ""
                if imported_module.endswith(".")
                else "."
            )
            imported_modules.update(
                f"{imported_module}{separator}{alias.name}"
                for alias in node.names
            )

    assert not {
        module
        for module in imported_modules
        if (
            module == "villaz_router.http_api.models"
            or module.startswith(
                "villaz_router.http_api.models."
            )
            or module == ".models"
            or module.startswith(".models.")
            or module == "pydantic"
            or module.startswith("pydantic.")
        )
    }


def test_exact_limit_calls_downstream() -> None:
    request_messages: list[Message] = [{
        "type": "http.request",
        "body": b"a" * MAX_REQUEST_BODY_BYTES,
        "more_body": False,
    }]

    calls, received, sent = run_http_middleware(
        request_messages
    )

    assert calls == 1
    assert received == request_messages
    assert response_status(sent) == 204


def test_one_byte_over_limit_returns_413() -> None:
    calls, received, sent = run_http_middleware([{
        "type": "http.request",
        "body": b"a" * (MAX_REQUEST_BODY_BYTES + 1),
        "more_body": False,
    }])

    assert calls == 0
    assert received == []
    assert response_status(sent) == 413
    assert response_payload(sent) == {
        "error": {
            "code": "REQUEST_TOO_LARGE",
            "message": (
                "The request body exceeds the maximum "
                "allowed size."
            ),
        }
    }


def test_limit_is_enforced_across_multiple_chunks() -> None:
    calls, received, sent = run_http_middleware([
        {
            "type": "http.request",
            "body": b"a" * 32_768,
            "more_body": True,
        },
        {
            "type": "http.request",
            "body": b"b" * 32_769,
            "more_body": False,
        },
    ])

    assert calls == 0
    assert received == []
    assert response_status(sent) == 413


def test_downstream_is_never_called_when_limit_is_exceeded() -> None:
    calls, _, _ = run_http_middleware([{
        "type": "http.request",
        "body": b"a" * (MAX_REQUEST_BODY_BYTES + 1),
        "more_body": True,
    }])

    assert calls == 0


def test_valid_request_events_are_replayed_unchanged() -> None:
    request_messages: list[Message] = [
        {
            "type": "http.request",
            "body": b"first",
            "more_body": True,
        },
        {
            "type": "http.request",
            "body": b"second",
            "more_body": False,
        },
    ]

    calls, received, _ = run_http_middleware(
        request_messages
    )

    assert calls == 1
    assert received == request_messages
    assert all(
        replayed is original
        for replayed, original in zip(
            received,
            request_messages,
            strict=True,
        )
    )


def test_empty_request_body_reaches_downstream() -> None:
    request_messages: list[Message] = [{
        "type": "http.request",
        "body": b"",
        "more_body": False,
    }]

    calls, received, sent = run_http_middleware(
        request_messages
    )

    assert calls == 1
    assert received == request_messages
    assert received[0] is request_messages[0]
    assert response_status(sent) == 204


def test_disconnect_as_first_event_reaches_downstream() -> None:
    request_messages: list[Message] = [{
        "type": "http.disconnect",
    }]

    calls, received, sent = run_http_middleware(
        request_messages
    )

    assert calls == 1
    assert received == request_messages
    assert received[0] is request_messages[0]
    assert response_status(sent) == 204


def test_disconnect_after_partial_body_reaches_downstream() -> None:
    request_messages: list[Message] = [
        {
            "type": "http.request",
            "body": b"partial",
            "more_body": True,
        },
        {
            "type": "http.disconnect",
        },
    ]

    calls, received, sent = run_http_middleware(
        request_messages
    )

    assert calls == 1
    assert received == request_messages
    assert all(
        replayed is original
        for replayed, original in zip(
            received,
            request_messages,
            strict=True,
        )
    )
    assert response_status(sent) == 204


def test_non_http_scope_passes_through_without_interference() -> None:
    downstream_calls = 0

    async def exercise() -> None:
        async def receive() -> Message:
            return {"type": "lifespan.startup"}

        async def send(message: Message) -> None:
            raise AssertionError("send must not be called")

        async def downstream(
            scope: Scope,
            received_receive: Receive,
            received_send: Send,
        ) -> None:
            nonlocal downstream_calls
            downstream_calls += 1
            assert scope["type"] == "lifespan"
            assert received_receive is receive
            assert received_send is send

        middleware = RequestBodyLimitMiddleware(
            downstream
        )
        scope: Scope = {
            "type": "lifespan",
            "asgi": {"version": "3.0"},
            "state": {},
        }
        await middleware(scope, receive, send)

    asyncio.run(exercise())
    assert downstream_calls == 1


def test_missing_content_length_does_not_bypass_limit() -> None:
    calls, _, sent = run_http_middleware([{
        "type": "http.request",
        "body": b"a" * (MAX_REQUEST_BODY_BYTES + 1),
        "more_body": False,
    }])

    assert calls == 0
    assert response_status(sent) == 413


def test_low_content_length_does_not_bypass_limit() -> None:
    calls, _, sent = run_http_middleware(
        [{
            "type": "http.request",
            "body": b"a" * (MAX_REQUEST_BODY_BYTES + 1),
            "more_body": False,
        }],
        headers=[(b"content-length", b"1")],
    )

    assert calls == 0
    assert response_status(sent) == 413


def test_high_content_length_does_not_reject_valid_body() -> None:
    calls, received, sent = run_http_middleware(
        [{
            "type": "http.request",
            "body": b"a",
            "more_body": False,
        }],
        headers=[(b"content-length", b"65537")],
    )

    assert calls == 1
    assert received[0]["body"] == b"a"
    assert response_status(sent) == 204


def test_prompt_message_over_character_limit_remains_422() -> None:
    endpoint_calls = 0
    application = FastAPI()
    application.add_middleware(
        RequestBodyLimitMiddleware
    )

    @application.post("/prompt")
    def prompt(request: PromptRequest) -> dict[str, bool]:
        nonlocal endpoint_calls
        endpoint_calls += 1
        return {"accepted": True}

    raw_body = json.dumps(
        {"message": "a" * 16_385},
        separators=(",", ":"),
    ).encode("utf-8")
    assert len(raw_body) < MAX_REQUEST_BODY_BYTES

    with TestClient(application) as client:
        response = client.post(
            "/prompt",
            content=raw_body,
            headers={
                "content-type": "application/json",
            },
        )

    assert response.status_code == 422
    assert endpoint_calls == 0
