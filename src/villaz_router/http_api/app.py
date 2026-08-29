from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from villaz_router.bootstrap import bootstrap_runtime
from villaz_router.http_api.routes import router


def create_app(
    configuration_root: str | Path | None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncIterator[None]:
        context = bootstrap_runtime(configuration_root)
        app.state.runtime_context = context

        try:
            yield
        finally:
            del app.state.runtime_context

    application = FastAPI(
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.include_router(router)

    return application
