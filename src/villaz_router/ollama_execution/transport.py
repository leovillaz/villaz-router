from typing import Protocol, runtime_checkable


@runtime_checkable
class OllamaTransport(Protocol):
    async def chat(
        self,
        payload: dict[str, object],
    ) -> object:
        ...

    async def aclose(self) -> None:
        ...
