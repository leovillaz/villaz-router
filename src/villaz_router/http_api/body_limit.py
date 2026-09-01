from collections import deque

from starlette.responses import JSONResponse
from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

MAX_REQUEST_BODY_BYTES = 65_536


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        received_bytes = 0
        received_messages: deque[Message] = deque()

        while True:
            message = await receive()
            received_messages.append(message)

            if message["type"] == "http.disconnect":
                break

            if message["type"] != "http.request":
                continue

            received_bytes += len(
                message.get("body", b"")
            )

            if received_bytes > MAX_REQUEST_BODY_BYTES:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "REQUEST_TOO_LARGE",
                            "message": (
                                "The request body exceeds the "
                                "maximum allowed size."
                            ),
                        }
                    },
                )
                await response(scope, receive, send)
                return

            if not message.get("more_body", False):
                break

        async def replay_receive() -> Message:
            if received_messages:
                return received_messages.popleft()
            return await receive()

        await self.app(scope, replay_receive, send)
