import ast
from pathlib import Path

import villaz_router
import villaz_router.http_api as http_api
from villaz_router.http_api.app import create_app
from villaz_router.http_api.dependencies import (
    get_runtime_context,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src" / "villaz_router"
HTTP_API_ROOT = PACKAGE_ROOT / "http_api"


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


def test_http_api_has_exact_public_exports() -> None:
    assert http_api.__all__ == [
        "create_app",
        "get_runtime_context",
    ]
    assert http_api.create_app is create_app
    assert (
        http_api.get_runtime_context
        is get_runtime_context
    )
    assert not hasattr(http_api, "LivenessResponse")
    assert not hasattr(http_api, "ReadinessResponse")


def test_core_package_does_not_export_http_symbols() -> None:
    assert "create_app" not in villaz_router.__all__
    assert (
        "get_runtime_context"
        not in villaz_router.__all__
    )
    assert not hasattr(villaz_router, "create_app")
    assert not hasattr(
        villaz_router,
        "get_runtime_context",
    )


def test_core_modules_do_not_import_http_adapter() -> None:
    violations = {
        path.name: sorted(
            module
            for module in imported_modules(path)
            if module.startswith(
                "villaz_router.http_api"
            )
        )
        for path in PACKAGE_ROOT.glob("*.py")
        if path.name not in {"cli.py", "__main__.py"}
    }

    assert not {
        name: modules
        for name, modules in violations.items()
        if modules
    }


def test_http_adapter_does_not_bypass_bootstrap() -> None:
    forbidden = {
        "villaz_router.loader",
        "villaz_router.registry_loader",
        "villaz_router.runtime_compatibility",
    }

    violations = {
        path.name: sorted(
            imported_modules(path) & forbidden
        )
        for path in HTTP_API_ROOT.glob("*.py")
    }

    assert not {
        name: modules
        for name, modules in violations.items()
        if modules
    }


def test_cli_is_only_root_http_composition_module() -> None:
    importers = {
        path.name
        for path in PACKAGE_ROOT.glob("*.py")
        if any(
            module.startswith("villaz_router.http_api")
            for module in imported_modules(path)
        )
    }

    assert importers == {"cli.py"}


def test_cli_is_only_root_uvicorn_importer() -> None:
    importers = {
        path.name
        for path in PACKAGE_ROOT.glob("*.py")
        if "uvicorn" in imported_modules(path)
    }

    assert importers == {"cli.py"}


def test_only_router_adapter_imports_router_directly() -> None:
    router_importers = {
        path.name
        for path in HTTP_API_ROOT.glob("*.py")
        if "villaz_router.router" in imported_modules(path)
    }

    assert router_importers == {"router_adapter.py"}


def test_only_routes_imports_dispatcher_directly() -> None:
    dispatcher_importers = {
        path.name
        for path in HTTP_API_ROOT.glob("*.py")
        if "villaz_router.dispatcher" in imported_modules(path)
    }

    assert dispatcher_importers == {"routes.py"}


def test_router_adapter_has_no_forbidden_execution_dependencies() -> None:
    path = HTTP_API_ROOT / "router_adapter.py"
    forbidden_prefixes = (
        "fastapi",
        "starlette.responses",
        "villaz_router.dispatcher",
        "villaz_router.dispatcher_models",
        "villaz_router.loader",
        "villaz_router.ollama_execution",
        "villaz_router.registry_loader",
        "villaz_router.runtime_compatibility",
    )
    violations = {
        module
        for module in imported_modules(path)
        if module.startswith(forbidden_prefixes)
    }

    assert not violations, (
        "router adapter imports forbidden execution dependencies: "
        f"{violations}"
    )


def test_http_adapter_has_no_infrastructure_imports() -> None:
    forbidden_roots = {
        "httpx",
        "httpx2",
        "ollama",
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
        for path in HTTP_API_ROOT.glob("*.py")
    }

    assert not {
        name: modules
        for name, modules in violations.items()
        if modules
    }


def test_routes_do_not_access_application_state() -> None:
    source = (
        HTTP_API_ROOT / "routes.py"
    ).read_text(encoding="utf-8")

    assert ".state" not in source


def test_routes_do_not_import_runtime_infrastructure() -> None:
    path = HTTP_API_ROOT / "routes.py"
    forbidden_prefixes = (
        "httpx",
        "villaz_router.loader",
        "villaz_router.ollama_execution.config_loader",
        "villaz_router.ollama_execution.factory",
        "villaz_router.ollama_execution.transport",
        "villaz_router.registry_loader",
        "villaz_router.runtime_compatibility",
    )
    violations = {
        module
        for module in imported_modules(path)
        if module.startswith(forbidden_prefixes)
    }

    assert not violations, (
        "routes import forbidden runtime infrastructure: "
        f"{violations}"
    )


def test_app_module_has_no_global_application() -> None:
    path = HTTP_API_ROOT / "app.py"
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    assigned_names: set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                assigned_names.add(node.target.id)

    assert "app" not in assigned_names
    assert "application" not in assigned_names
