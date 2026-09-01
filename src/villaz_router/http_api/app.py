from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from villaz_router.bootstrap import bootstrap_runtime
from villaz_router.http_api.body_limit import (
    RequestBodyLimitMiddleware,
)
from villaz_router.ollama_execution.config_loader import (
    load_ollama_client_config,
)
from villaz_router.ollama_execution.factory import (
    create_ollama_executor,
)
from villaz_router.http_api.routes import router


def create_app(
    configuration_root: str | Path | None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[None, None]:
        context = bootstrap_runtime(
            configuration_root
        )
        ollama_config = load_ollama_client_config(
            context.configuration_root
        )
        ollama_executor = create_ollama_executor(
            ollama_config
        )

        app.state.runtime_context = context
        app.state.ollama_executor = ollama_executor

        try:
            yield
        finally:
            try:
                await ollama_executor.aclose()
            finally:
                del app.state.ollama_executor
                del app.state.runtime_context

    application = FastAPI(
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.add_middleware(
        RequestBodyLimitMiddleware
    )
    application.include_router(router)

    return application
