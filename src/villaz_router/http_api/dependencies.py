from fastapi import Request

from villaz_router.bootstrap_models import RuntimeContext

from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)

def get_runtime_context(request: Request) -> RuntimeContext:
    try:
        context = request.app.state.runtime_context
    except AttributeError as exc:
        raise RuntimeError(
            "runtime context is unavailable outside "
            "the active application lifespan"
        ) from exc

    if not isinstance(context, RuntimeContext):
        raise TypeError(
            "app.state.runtime_context must be "
            "a RuntimeContext instance"
        )

    return context

def get_ollama_executor(
    request: Request,
) -> OllamaExecutor:
    try:
        executor = request.app.state.ollama_executor
    except AttributeError as exc:
        raise RuntimeError(
            "ollama executor is unavailable outside "
            "the active application lifespan"
        ) from exc

    if not isinstance(executor, OllamaExecutor):
        raise TypeError(
            "app.state.ollama_executor must be "
            "an OllamaExecutor instance"
        )

    return executor
