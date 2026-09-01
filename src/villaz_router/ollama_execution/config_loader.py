from pathlib import Path
from typing import Any

import yaml

from villaz_router.ollama_execution.config import (
    OllamaClientConfig,
    OllamaConnectionLimits,
    OllamaTimeoutConfig,
)


def _read_ollama_config(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def load_ollama_client_config(
    configuration_root: Path,
) -> OllamaClientConfig:
    path = (
        configuration_root.resolve()
        / "config"
        / "ollama.yaml"
    )

    raw = _read_ollama_config(path)

    if not isinstance(raw, dict):
        raise ValueError(
            "ollama configuration must be a mapping"
        )

    timeouts = OllamaTimeoutConfig.model_validate(
        raw.get("timeouts")
    )
    limits = OllamaConnectionLimits.model_validate(
        raw.get("limits")
    )

    client_raw = dict(raw)
    client_raw["timeouts"] = timeouts
    client_raw["limits"] = limits

    return OllamaClientConfig.model_validate(
        client_raw
    )
