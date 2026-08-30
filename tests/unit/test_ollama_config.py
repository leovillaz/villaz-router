from typing import Any

import pytest
from pydantic import ValidationError

from villaz_router.ollama_execution.config import (
    OllamaClientConfig,
    OllamaConnectionLimits,
    OllamaTimeoutConfig,
)


def make_timeouts() -> OllamaTimeoutConfig:
    return OllamaTimeoutConfig(
        connect_seconds=5.0,
        read_seconds=300.0,
        write_seconds=10.0,
        pool_seconds=5.0,
    )


def make_limits() -> OllamaConnectionLimits:
    return OllamaConnectionLimits(
        max_connections=1,
        max_keepalive_connections=1,
        keepalive_expiry_seconds=30.0,
    )


def make_client_config() -> OllamaClientConfig:
    return OllamaClientConfig(
        base_url="http://127.0.0.1:11434",
        timeouts=make_timeouts(),
        limits=make_limits(),
    )


@pytest.mark.parametrize(
    ("model_type", "expected_fields"),
    [
        (
            OllamaTimeoutConfig,
            {
                "connect_seconds",
                "read_seconds",
                "write_seconds",
                "pool_seconds",
            },
        ),
        (
            OllamaConnectionLimits,
            {
                "max_connections",
                "max_keepalive_connections",
                "keepalive_expiry_seconds",
            },
        ),
        (
            OllamaClientConfig,
            {
                "base_url",
                "timeouts",
                "limits",
            },
        ),
    ],
)
def test_config_models_have_exact_contract(
    model_type: type[
        OllamaTimeoutConfig
        | OllamaConnectionLimits
        | OllamaClientConfig
    ],
    expected_fields: set[str],
) -> None:
    assert set(model_type.model_fields) == expected_fields
    assert model_type.model_config["extra"] == "forbid"
    assert model_type.model_config["frozen"] is True
    assert model_type.model_config["strict"] is True
    assert all(
        field.is_required()
        for field in model_type.model_fields.values()
    )


def test_operational_configuration_is_preserved() -> None:
    timeouts = make_timeouts()
    limits = make_limits()
    config = make_client_config()

    assert timeouts.model_dump() == {
        "connect_seconds": 5.0,
        "read_seconds": 300.0,
        "write_seconds": 10.0,
        "pool_seconds": 5.0,
    }
    assert limits.model_dump() == {
        "max_connections": 1,
        "max_keepalive_connections": 1,
        "keepalive_expiry_seconds": 30.0,
    }
    assert config.base_url == (
        "http://127.0.0.1:11434"
    )


def test_client_config_preserves_nested_identity() -> None:
    timeouts = make_timeouts()
    limits = make_limits()

    config = OllamaClientConfig(
        base_url="http://127.0.0.1:11434",
        timeouts=timeouts,
        limits=limits,
    )

    assert config.timeouts is timeouts
    assert config.limits is limits


@pytest.mark.parametrize(
    "model",
    [
        pytest.param(
            make_timeouts(),
            id="timeouts",
        ),
        pytest.param(
            make_limits(),
            id="limits",
        ),
        pytest.param(
            make_client_config(),
            id="client",
        ),
    ],
)
def test_config_models_are_frozen(
    model: (
        OllamaTimeoutConfig
        | OllamaConnectionLimits
        | OllamaClientConfig
    ),
) -> None:
    field_name = next(
    iter(type(model).model_fields)
)

    with pytest.raises(ValidationError):
        setattr(model, field_name, "changed")


def test_config_models_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        OllamaTimeoutConfig.model_validate({
            "connect_seconds": 5.0,
            "read_seconds": 300.0,
            "write_seconds": 10.0,
            "pool_seconds": 5.0,
            "unexpected": True,
        })

    with pytest.raises(ValidationError):
        OllamaConnectionLimits.model_validate({
            "max_connections": 1,
            "max_keepalive_connections": 1,
            "keepalive_expiry_seconds": 30.0,
            "unexpected": True,
        })

    with pytest.raises(ValidationError):
        OllamaClientConfig.model_validate({
            "base_url": "http://127.0.0.1:11434",
            "timeouts": make_timeouts(),
            "limits": make_limits(),
            "unexpected": True,
        })


@pytest.mark.parametrize(
    "field_name",
    [
        "connect_seconds",
        "read_seconds",
        "write_seconds",
        "pool_seconds",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_timeouts_require_positive_finite_values(
    field_name: str,
    invalid_value: float,
) -> None:
    values = {
        "connect_seconds": 5.0,
        "read_seconds": 300.0,
        "write_seconds": 10.0,
        "pool_seconds": 5.0,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        OllamaTimeoutConfig.model_validate(values)


@pytest.mark.parametrize(
    "invalid_value",
    [
        1,
        "5.0",
        True,
        None,
    ],
)
def test_timeouts_require_exact_float_type(
    invalid_value: Any,
) -> None:
    with pytest.raises(ValidationError):
        OllamaTimeoutConfig(
            connect_seconds=invalid_value,
            read_seconds=300.0,
            write_seconds=10.0,
            pool_seconds=5.0,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "max_connections",
        "max_keepalive_connections",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        1.0,
        "1",
        True,
        None,
    ],
)
def test_connection_counts_require_exact_int_type(
    field_name: str,
    invalid_value: Any,
) -> None:
    values: dict[str, Any] = {
        "max_connections": 1,
        "max_keepalive_connections": 1,
        "keepalive_expiry_seconds": 30.0,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        OllamaConnectionLimits.model_validate(values)


@pytest.mark.parametrize(
    "invalid_value",
    [
        0,
        -1,
    ],
)
def test_max_connections_must_be_positive(
    invalid_value: int,
) -> None:
    with pytest.raises(ValidationError):
        OllamaConnectionLimits(
            max_connections=invalid_value,
            max_keepalive_connections=0,
            keepalive_expiry_seconds=30.0,
        )


def test_max_keepalive_connections_must_not_be_negative() -> None:
    with pytest.raises(ValidationError):
        OllamaConnectionLimits(
            max_connections=1,
            max_keepalive_connections=-1,
            keepalive_expiry_seconds=30.0,
        )


def test_keepalive_count_must_not_exceed_connection_count() -> None:
    with pytest.raises(ValidationError):
        OllamaConnectionLimits(
            max_connections=1,
            max_keepalive_connections=2,
            keepalive_expiry_seconds=30.0,
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        30,
        "30.0",
        True,
        None,
    ],
)
def test_keepalive_expiry_requires_positive_finite_float(
    invalid_value: Any,
) -> None:
    with pytest.raises(ValidationError):
        OllamaConnectionLimits(
            max_connections=1,
            max_keepalive_connections=1,
            keepalive_expiry_seconds=invalid_value,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:11434",
        "http://localhost:11434",
        "https://ollama.internal:11434",
        "http://[::1]:11434",
        "http://localhost/",
    ],
)
def test_base_url_accepts_valid_service_roots(
    base_url: str,
) -> None:
    config = OllamaClientConfig(
        base_url=base_url,
        timeouts=make_timeouts(),
        limits=make_limits(),
    )

    assert config.base_url == base_url


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        " ",
        "127.0.0.1:11434",
        "ftp://127.0.0.1:11434",
        "http:///api",
        "http://user@127.0.0.1:11434",
        "http://user:secret@127.0.0.1:11434",
        "http://127.0.0.1:11434?mode=test",
        "http://127.0.0.1:11434?",
        "http://127.0.0.1:11434#fragment",
        "http://127.0.0.1:11434#",
        "http://127.0.0.1:11434/api",
        "http://127.0.0.1:11434/api/generate",
        "http://127.0.0.1:11434 ",
        "http://127.0.0.1:",
        "http://127.0.0.1:70000",
        "http://[::1",
    ],
)
def test_base_url_rejects_invalid_or_unsafe_values(
    base_url: str,
) -> None:
    with pytest.raises(ValidationError):
        OllamaClientConfig(
            base_url=base_url,
            timeouts=make_timeouts(),
            limits=make_limits(),
        )


def test_base_url_requires_exact_string_type() -> None:
    with pytest.raises(ValidationError):
        OllamaClientConfig(
            base_url=11434,
            timeouts=make_timeouts(),
            limits=make_limits(),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        (
            "timeouts",
            {
                "connect_seconds": 5.0,
                "read_seconds": 300.0,
                "write_seconds": 10.0,
                "pool_seconds": 5.0,
            },
        ),
        (
            "limits",
            {
                "max_connections": 1,
                "max_keepalive_connections": 1,
                "keepalive_expiry_seconds": 30.0,
            },
        ),
    ],
)
def test_client_config_rejects_nested_mappings(
    field_name: str,
    value: dict[str, Any],
) -> None:
    values: dict[str, Any] = {
        "base_url": "http://127.0.0.1:11434",
        "timeouts": make_timeouts(),
        "limits": make_limits(),
    }
    values[field_name] = value

    with pytest.raises(ValidationError):
        OllamaClientConfig.model_validate(values)
