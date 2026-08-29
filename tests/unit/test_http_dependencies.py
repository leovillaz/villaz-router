import inspect
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.http_api.dependencies import get_runtime_context
from villaz_router.models import RulesetSnapshot
from villaz_router.registry_models import ProfileRegistrySnapshot


def make_runtime_context(root: Path) -> RuntimeContext:
    return RuntimeContext.model_construct(
        configuration_root=root,
        ruleset=RulesetSnapshot.model_construct(),
        profile_registry=(
            ProfileRegistrySnapshot.model_construct()
        ),
    )


def make_request(app: FastAPI) -> Request:
    return Request({
        "type": "http",
        "app": app,
    })


def test_get_runtime_context_has_exact_sync_contract() -> None:
    signature = inspect.signature(get_runtime_context)

    assert tuple(signature.parameters) == ("request",)
    assert signature.parameters["request"].annotation is Request
    assert signature.return_annotation is RuntimeContext
    assert not inspect.iscoroutinefunction(get_runtime_context)


def test_get_runtime_context_preserves_identity(
    tmp_path: Path,
) -> None:
    app = FastAPI()
    context = make_runtime_context(tmp_path.resolve())
    app.state.runtime_context = context

    result = get_runtime_context(make_request(app))

    assert result is context
    assert app.state.runtime_context is context


def test_get_runtime_context_does_not_cache_result(
    tmp_path: Path,
) -> None:
    app = FastAPI()
    first = make_runtime_context(
        (tmp_path / "first").resolve()
    )
    second = make_runtime_context(
        (tmp_path / "second").resolve()
    )
    request = make_request(app)

    app.state.runtime_context = first
    first_result = get_runtime_context(request)

    app.state.runtime_context = second
    second_result = get_runtime_context(request)

    assert first_result is first
    assert second_result is second


def test_missing_runtime_context_raises_runtime_error() -> None:
    app = FastAPI()

    with pytest.raises(RuntimeError) as exc_info:
        get_runtime_context(make_request(app))

    error = exc_info.value

    assert error.args == (
        "runtime context is unavailable outside "
        "the active application lifespan",
    )
    assert str(error) == (
        "runtime context is unavailable outside "
        "the active application lifespan"
    )
    assert isinstance(error.__cause__, AttributeError)


@pytest.mark.parametrize(
    "invalid_context",
    [
        None,
        "invalid",
        object(),
        {},
    ],
)
def test_invalid_runtime_context_type_raises_type_error(
    invalid_context: Any,
) -> None:
    app = FastAPI()
    app.state.runtime_context = invalid_context

    with pytest.raises(TypeError) as exc_info:
        get_runtime_context(make_request(app))

    error = exc_info.value

    assert error.args == (
        "app.state.runtime_context must be "
        "a RuntimeContext instance",
    )
    assert str(error) == (
        "app.state.runtime_context must be "
        "a RuntimeContext instance"
    )
    assert error.__cause__ is None
