from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from villaz_router.ollama_execution.config_loader import (
    load_ollama_client_config,
)


def write_config(
    root: Path,
    content: str,
) -> Path:
    config_dir = root / "config"
    config_dir.mkdir()

    path = config_dir / "ollama.yaml"
    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def valid_config_text() -> str:
    return (
        "base_url: http://127.0.0.1:11434\n"
        "\n"
        "timeouts:\n"
        "  connect_seconds: 5.0\n"
        "  read_seconds: 300.0\n"
        "  write_seconds: 10.0\n"
        "  pool_seconds: 5.0\n"
        "\n"
        "limits:\n"
        "  max_connections: 1\n"
        "  max_keepalive_connections: 1\n"
        "  keepalive_expiry_seconds: 30.0\n"
    )


def test_loads_official_ollama_configuration(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        valid_config_text(),
    )

    config = load_ollama_client_config(
        tmp_path
    )

    assert config.base_url == (
        "http://127.0.0.1:11434"
    )
    assert config.timeouts.model_dump() == {
        "connect_seconds": 5.0,
        "read_seconds": 300.0,
        "write_seconds": 10.0,
        "pool_seconds": 5.0,
    }
    assert config.limits.model_dump() == {
        "max_connections": 1,
        "max_keepalive_connections": 1,
        "keepalive_expiry_seconds": 30.0,
    }


def test_missing_configuration_file_propagates(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        load_ollama_client_config(tmp_path)


def test_invalid_yaml_propagates(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        "base_url: [\n",
    )

    with pytest.raises(yaml.YAMLError):
        load_ollama_client_config(tmp_path)


def test_document_must_be_mapping(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        "- invalid\n- document\n",
    )

    with pytest.raises(
        ValueError,
        match=(
            "ollama configuration "
            "must be a mapping"
        ),
    ):
        load_ollama_client_config(tmp_path)


def test_invalid_nested_configuration_propagates(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        valid_config_text().replace(
            "read_seconds: 300.0",
            "read_seconds: 300",
        ),
    )

    with pytest.raises(ValidationError):
        load_ollama_client_config(tmp_path)


def test_unexpected_top_level_field_is_rejected(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        (
            valid_config_text()
            + "unexpected: true\n"
        ),
    )

    with pytest.raises(ValidationError):
        load_ollama_client_config(tmp_path)


def test_loader_does_not_modify_source_file(
    tmp_path: Path,
) -> None:
    original = valid_config_text()
    path = write_config(
        tmp_path,
        original,
    )

    load_ollama_client_config(tmp_path)

    assert path.read_text(
        encoding="utf-8"
    ) == original
