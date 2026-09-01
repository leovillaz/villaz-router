import ast
from pathlib import Path
import tomllib

import villaz_router
import villaz_router.ollama_execution as ollama_execution
from villaz_router.ollama_execution.config import (
    OllamaClientConfig,
    OllamaConnectionLimits,
    OllamaTimeoutConfig,
)
from villaz_router.ollama_execution.errors import (
    OllamaExecutionError,
    OllamaExecutionErrorCode,
    OllamaExecutionStage,
    OllamaTransportError,
    OllamaTransportErrorCode,
)
from villaz_router.ollama_execution.executor import OllamaExecutor
from villaz_router.ollama_execution.factory import (
    create_ollama_executor,
)
from villaz_router.ollama_execution.models import (
    OllamaExecutionRequest,
    OllamaExecutionResult,
)
from villaz_router.ollama_execution.transport import OllamaTransport


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src" / "villaz_router"
HTTP_API_ROOT = PACKAGE_ROOT / "http_api"
OLLAMA_ROOT = PACKAGE_ROOT / "ollama_execution"

EXPECTED_FILES = {
    "__init__.py",
    "config.py",
    "config_loader.py",
    "errors.py",
    "executor.py",
    "factory.py",
    "httpx2_transport.py",
    "models.py",
    "transport.py",
}

EXPECTED_EXPORTS = [
    "OllamaClientConfig",
    "OllamaConnectionLimits",
    "OllamaExecutionError",
    "OllamaExecutionErrorCode",
    "OllamaExecutionRequest",
    "OllamaExecutionResult",
    "OllamaExecutionStage",
    "OllamaExecutor",
    "OllamaTimeoutConfig",
    "OllamaTransport",
    "OllamaTransportError",
    "OllamaTransportErrorCode",
    "create_ollama_executor",
]

EXPECTED_SYMBOLS = {
    "OllamaClientConfig": OllamaClientConfig,
    "OllamaConnectionLimits": OllamaConnectionLimits,
    "OllamaExecutionError": OllamaExecutionError,
    "OllamaExecutionErrorCode": OllamaExecutionErrorCode,
    "OllamaExecutionRequest": OllamaExecutionRequest,
    "OllamaExecutionResult": OllamaExecutionResult,
    "OllamaExecutionStage": OllamaExecutionStage,
    "OllamaExecutor": OllamaExecutor,
    "OllamaTimeoutConfig": OllamaTimeoutConfig,
    "OllamaTransport": OllamaTransport,
    "OllamaTransportError": OllamaTransportError,
    "OllamaTransportErrorCode": OllamaTransportErrorCode,
    "create_ollama_executor": create_ollama_executor,
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(
                alias.name
                for alias in node.names
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
        ):
            modules.add(node.module)

    return modules


def test_ollama_package_has_exact_module_set() -> None:
    assert {
        path.name
        for path in OLLAMA_ROOT.glob("*.py")
    } == EXPECTED_FILES


def test_ollama_package_has_exact_public_exports() -> None:
    assert ollama_execution.__all__ == EXPECTED_EXPORTS

    for name, symbol in EXPECTED_SYMBOLS.items():
        assert getattr(ollama_execution, name) is symbol


def test_concrete_httpx2_transport_is_internal() -> None:
    assert (
        "Httpx2OllamaTransport"
        not in ollama_execution.__all__
    )
    assert not hasattr(
        ollama_execution,
        "Httpx2OllamaTransport",
    )


def test_core_package_does_not_export_ollama_symbols() -> None:
    for name in EXPECTED_EXPORTS:
        assert name not in villaz_router.__all__
        assert not hasattr(villaz_router, name)


def test_core_modules_do_not_import_ollama_execution() -> None:
    violations = {
        path.name: sorted(
            module
            for module in imported_modules(path)
            if module.startswith(
                "villaz_router.ollama_execution"
            )
        )
        for path in PACKAGE_ROOT.glob("*.py")
    }

    assert not {
        name: modules
        for name, modules in violations.items()
        if modules
    }


def test_only_approved_http_modules_import_ollama_execution() -> None:
    importers = {
        path.name
        for path in HTTP_API_ROOT.glob("*.py")
        if any(
            module.startswith(
                "villaz_router.ollama_execution"
            )
            for module in imported_modules(path)
        )
    }

    assert importers == {
        "app.py",
        "dependencies.py",
        "routes.py",
    }


def test_only_concrete_transport_and_factory_import_httpx2() -> None:
    importers = {
        path.name
        for path in OLLAMA_ROOT.glob("*.py")
        if any(
            module.split(".", 1)[0] == "httpx2"
            for module in imported_modules(path)
        )
    }

    assert importers == {
        "factory.py",
        "httpx2_transport.py",
    }


def test_executor_remains_independent_of_concrete_transport() -> None:
    imports = imported_modules(
        OLLAMA_ROOT / "executor.py"
    )

    assert "httpx2" not in {
        module.split(".", 1)[0]
        for module in imports
    }
    assert (
        "villaz_router.ollama_execution.httpx2_transport"
        not in imports
    )


def test_ollama_package_has_no_forbidden_infrastructure() -> None:
    forbidden_roots = {
        "fastapi",
        "httpx",
        "logging",
        "ollama",
        "os",
        "requests",
        "sqlite3",
        "starlette",
        "subprocess",
        "uvicorn",
    }

    violations = {
        path.name: sorted(
            module
            for module in imported_modules(path)
            if module.split(".", 1)[0]
            in forbidden_roots
        )
        for path in OLLAMA_ROOT.glob("*.py")
    }

    assert not {
        name: modules
        for name, modules in violations.items()
        if modules
    }


def test_config_loader_has_exact_import_boundary() -> None:
    assert imported_modules(
        OLLAMA_ROOT / "config_loader.py"
    ) == {
        "pathlib",
        "typing",
        "yaml",
        "villaz_router.ollama_execution.config",
    }


def test_only_generate_endpoint_is_present() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in OLLAMA_ROOT.glob("*.py")
    )

    assert source.count("/api/generate") == 1

    for forbidden_endpoint in (
        "/api/version",
        "/api/tags",
        "/api/ps",
        "/api/show",
        "/api/pull",
        "/api/create",
        "/api/delete",
    ):
        assert forbidden_endpoint not in source


def test_ollama_package_contains_no_credential_headers() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in OLLAMA_ROOT.glob("*.py")
    )

    assert "Authorization" not in source
    assert "Cookie" not in source
    assert "Bearer " not in source


def test_dependency_placement_is_exact() -> None:
    document = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    runtime_dependencies = document["project"]["dependencies"]
    development_dependencies = (
        document["project"]["optional-dependencies"]["dev"]
    )

    assert "httpx2==2.12.0" in runtime_dependencies
    assert "httpx2==2.12.0" not in development_dependencies
    assert "anyio==4.14.2" in development_dependencies

    all_dependencies = (
        runtime_dependencies
        + development_dependencies
    )

    assert not any(
        dependency.lower().startswith("httpx==")
        for dependency in all_dependencies
    )
    assert not any(
        dependency.lower().startswith("ollama")
        for dependency in all_dependencies
    )
