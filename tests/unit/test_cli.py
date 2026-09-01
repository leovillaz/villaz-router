from contextlib import contextmanager
from pathlib import Path
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from villaz_router import cli
from villaz_router.bootstrap_errors import (
    ApplicationBootstrapError,
)


ROOT = Path(__file__).resolve().parents[2]


def install_fake_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
    run,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "uvicorn",
        SimpleNamespace(run=run),
    )


def test_top_level_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])

    assert error.value.code == 0
    assert "serve" in capsys.readouterr().out


def test_serve_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["serve", "--help"])

    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "--host" in output
    assert "--port" in output
    assert "--configuration-root" in output


def test_default_serve_uses_packaged_root_and_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application = object()
    calls: list[tuple[object, Path, str, int]] = []

    def fake_create_app(root: Path) -> object:
        assert root != tmp_path
        assert (root / "config" / "router.yaml").is_file()
        calls.append((application, root, "", 0))
        return application

    def fake_run(
        received_app: object,
        *,
        host: str,
        port: int,
    ) -> None:
        created = calls[0]
        calls[0] = (received_app, created[1], host, port)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "create_app", fake_create_app)
    install_fake_uvicorn(monkeypatch, fake_run)

    assert cli.main(["serve"]) == 0
    assert calls == [
        (application, calls[0][1], "127.0.0.1", 8000)
    ]
    assert capsys.readouterr().err == ""


def test_packaged_resource_lifetime_covers_uvicorn_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = False

    @contextmanager
    def fake_packaged_root():
        nonlocal active
        active = True
        try:
            yield tmp_path
        finally:
            active = False

    monkeypatch.setattr(
        cli,
        "packaged_configuration_root",
        fake_packaged_root,
    )
    monkeypatch.setattr(
        cli,
        "create_app",
        lambda root: object(),
    )

    def fake_run(app: object, **options: object) -> None:
        assert active

    install_fake_uvicorn(monkeypatch, fake_run)

    assert cli.main(["serve"]) == 0
    assert not active


def test_override_is_absolute_and_does_not_use_packaged_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    override = tmp_path / "configuration"
    override.mkdir()
    captured: list[Path] = []

    def fail_if_resolved():
        raise AssertionError(
            "override must not resolve packaged data"
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "packaged_configuration_root",
        fail_if_resolved,
    )
    monkeypatch.setattr(
        cli,
        "create_app",
        lambda root: captured.append(root) or object(),
    )
    install_fake_uvicorn(
        monkeypatch,
        lambda app, **options: None,
    )

    assert cli.main([
        "serve",
        "--configuration-root",
        "configuration",
    ]) == 0
    assert captured == [override.resolve()]


def test_incomplete_override_fails_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_resolved():
        raise AssertionError(
            "invalid override must not use packaged data"
        )

    def start_lifespan(app: object, **options: object) -> None:
        with TestClient(app):
            pass

    monkeypatch.setattr(
        cli,
        "packaged_configuration_root",
        fail_if_resolved,
    )
    install_fake_uvicorn(monkeypatch, start_lifespan)

    with pytest.raises(ApplicationBootstrapError):
        cli.main([
            "serve",
            "--configuration-root",
            str(tmp_path),
        ])


def test_custom_host_and_port_reach_uvicorn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[str, int]] = []

    monkeypatch.setattr(
        cli,
        "create_app",
        lambda root: object(),
    )
    install_fake_uvicorn(
        monkeypatch,
        lambda app, host, port: captured.append(
            (host, port)
        ),
    )

    assert cli.main([
        "serve",
        "--host",
        "0.0.0.0",
        "--port",
        "9000",
        "--configuration-root",
        str(tmp_path),
    ]) == 0
    assert captured == [("0.0.0.0", 9000)]


@pytest.mark.parametrize(
    "host",
    ["127.0.0.1", "127.0.0.2", "::1", "localhost"],
)
def test_loopback_hosts_do_not_warn(
    host: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli,
        "create_app",
        lambda root: object(),
    )
    install_fake_uvicorn(
        monkeypatch,
        lambda app, **options: None,
    )

    assert cli.main([
        "serve",
        "--host",
        host,
        "--configuration-root",
        str(tmp_path),
    ]) == 0
    assert capsys.readouterr().err == ""


def test_non_loopback_host_warns_without_sensitive_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli,
        "create_app",
        lambda root: object(),
    )
    install_fake_uvicorn(
        monkeypatch,
        lambda app, **options: None,
    )

    assert cli.main([
        "serve",
        "--host",
        "0.0.0.0",
        "--configuration-root",
        str(tmp_path),
    ]) == 0

    warning = capsys.readouterr().err
    assert "non-loopback" in warning
    assert str(tmp_path) not in warning
    assert "prompt" not in warning.casefold()
    assert "token" not in warning.casefold()


def test_module_entrypoint_reuses_cli_main() -> None:
    import villaz_router.__main__ as module_entrypoint

    assert module_entrypoint.main is cli.main


def test_pyproject_registers_runtime_dependency_and_script() -> None:
    import tomllib

    document = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    assert "uvicorn==0.52.4" in (
        document["project"]["dependencies"]
    )
    assert "uvicorn==0.52.4" not in (
        document["project"][
            "optional-dependencies"
        ]["dev"]
    )
    assert document["project"]["scripts"] == {
        "villaz-router": "villaz_router.cli:main"
    }
