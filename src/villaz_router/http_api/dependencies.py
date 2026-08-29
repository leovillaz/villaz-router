from fastapi import Request

from villaz_router.bootstrap_models import RuntimeContext


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
