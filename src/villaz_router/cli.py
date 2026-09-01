import argparse
from collections.abc import Callable, Sequence
from ipaddress import ip_address
from pathlib import Path
import sys

from villaz_router.http_api import create_app
from villaz_router.runtime_resources import (
    packaged_configuration_root,
)


_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000
_EXPOSURE_WARNING = (
    "WARNING: binding to a non-loopback host may expose "
    "the unauthenticated API to other systems."
)


def _absolute_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "port must be an integer"
        ) from exc

    if not 1 <= port <= 65_535:
        raise argparse.ArgumentTypeError(
            "port must be between 1 and 65535"
        )

    return port


def _is_loopback_host(host: str) -> bool:
    if host.casefold() == "localhost":
        return True

    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _run_server(
    configuration_root: Path,
    host: str,
    port: int,
) -> int:
    if not _is_loopback_host(host):
        print(_EXPOSURE_WARNING, file=sys.stderr)

    application = create_app(configuration_root)

    import uvicorn

    uvicorn.run(
        application,
        host=host,
        port=port,
    )
    return 0


def _serve(arguments: argparse.Namespace) -> int:
    if arguments.configuration_root is not None:
        return _run_server(
            arguments.configuration_root,
            arguments.host,
            arguments.port,
        )

    with packaged_configuration_root() as root:
        return _run_server(
            root,
            arguments.host,
            arguments.port,
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="villaz-router",
        description="Run the Villaz Router application.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Run the HTTP application with Uvicorn.",
    )
    serve_parser.add_argument(
        "--host",
        default=_DEFAULT_HOST,
        help="Host to bind. Defaults to 127.0.0.1.",
    )
    serve_parser.add_argument(
        "--port",
        default=_DEFAULT_PORT,
        type=_port,
        help="Port to bind. Defaults to 8000.",
    )
    serve_parser.add_argument(
        "--configuration-root",
        type=_absolute_path,
        help=(
            "Use only this configuration tree instead of "
            "the packaged defaults."
        ),
    )
    serve_parser.set_defaults(handler=_serve)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = (
        arguments.handler
    )
    return handler(arguments)
