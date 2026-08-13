from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from villaz_router.config import RouterConfigDocument
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.models import (
    DomainsDocument,
    IntentsDocument,
    ProfilesDocument,
    RoutingDocument,
)


TModel = TypeVar("TModel", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class LoadedRulesetDocuments:
    config: RouterConfigDocument
    profiles: ProfilesDocument
    domains: DomainsDocument
    intents: IntentsDocument
    routing: RoutingDocument


def _read_yaml_file(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            f"required ruleset file not found: {path}",
        ) from exc
    except OSError as exc:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            f"unable to read ruleset file: {path}",
        ) from exc

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            f"invalid YAML syntax: {path}",
        ) from exc


def _parse_document(
    path: Path,
    model_type: type[TModel],
) -> TModel:
    raw = _read_yaml_file(path)

    if not isinstance(raw, dict):
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            f"ruleset document must be a mapping: {path}",
        )

    try:
        return model_type.model_validate(raw)
    except ValidationError as exc:
        raise RouterError(
            RouterErrorCode.INVALID_RULESET,
            f"ruleset schema validation failed: {path}",
        ) from exc


def load_ruleset_documents(
    project_root: Path,
) -> LoadedRulesetDocuments:
    root = project_root.resolve()

    return LoadedRulesetDocuments(
        config=_parse_document(
            root / "config" / "router.yaml",
            RouterConfigDocument,
        ),
        profiles=_parse_document(
            root / "rules" / "profiles.yaml",
            ProfilesDocument,
        ),
        domains=_parse_document(
            root / "rules" / "domains.yaml",
            DomainsDocument,
        ),
        intents=_parse_document(
            root / "rules" / "intents.yaml",
            IntentsDocument,
        ),
        routing=_parse_document(
            root / "rules" / "routing.yaml",
            RoutingDocument,
        ),
    )


def load_and_validate_ruleset_documents(
    project_root: Path,
) -> LoadedRulesetDocuments:
    documents = load_ruleset_documents(project_root)

    from villaz_router.validation import validate_ruleset_semantics

    validate_ruleset_semantics(documents)

    return documents
