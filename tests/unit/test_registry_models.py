import pytest
from pydantic import ValidationError

from villaz_router.registry_models import ProfileDefinition


def make_profile(**overrides):
    data = {
        "id": "mobile-dev",
        "enabled": True,
        "display_name": "Mobile Development",
        "description": "Perfil especializado em desenvolvimento mobile.",
        "model": "example-model:latest",
        "system_prompt": "Responda como especialista em desenvolvimento mobile.",
    }
    data.update(overrides)
    return ProfileDefinition(**data)


def test_profile_definition_accepts_valid_profile() -> None:
    profile = make_profile()

    assert profile.id == "mobile-dev"
    assert profile.enabled is True
    assert profile.display_name == "Mobile Development"
    assert profile.model == "example-model:latest"


@pytest.mark.parametrize(
    "profile_id",
    [
        "",
        "Mobile-Dev",
        "mobile_dev",
        "mobile dev",
        " mobile-dev",
        "mobile-dev ",
        "mobile--dev",
        "-mobile-dev",
        "mobile-dev-",
    ],
)
def test_profile_id_requires_canonical_kebab_case(
    profile_id: str,
) -> None:
    with pytest.raises(ValidationError):
        make_profile(id=profile_id)


@pytest.mark.parametrize(
    "field_name",
    [
        "display_name",
        "description",
        "model",
        "system_prompt",
    ],
)
@pytest.mark.parametrize("value", ["", "   ", chr(9), chr(10), " " + chr(10) + chr(9) + " "])
def test_required_text_fields_reject_empty_or_whitespace_only(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValidationError):
        make_profile(**{field_name: value})


def test_profile_definition_preserves_valid_whitespace() -> None:
    profile = make_profile(
        display_name=" Mobile Development ",
        system_prompt=" Linha 1.\\nLinha 2. ",
    )

    assert profile.display_name == " Mobile Development "
    assert profile.system_prompt == " Linha 1.\\nLinha 2. "


@pytest.mark.parametrize("enabled", [1, 0, "true", "false", None])
def test_enabled_is_strictly_boolean(enabled) -> None:
    with pytest.raises(ValidationError):
        make_profile(enabled=enabled)


def test_profile_definition_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        make_profile(temperature=0.2)


def test_profile_definition_is_immutable() -> None:
    profile = make_profile()

    with pytest.raises(ValidationError):
        profile.model = "other-model"
