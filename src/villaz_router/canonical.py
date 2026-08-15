from __future__ import annotations

import hashlib
import json
from typing import Any

from villaz_router.loader import LoadedRulesetDocuments
from villaz_router.models import (
    Domain,
    Intent,
    RulesetSnapshot,
)
from villaz_router.validation import validate_ruleset_semantics


def _canonical_evidence(
    items: tuple[Any, ...],
) -> list[dict[str, Any]]:
    return [
        evidence.model_dump(mode="json")
        for evidence in sorted(
            items,
            key=lambda item: item.id,
        )
    ]


def _canonical_domain(domain: Domain) -> dict[str, Any]:
    payload = domain.model_dump(
        mode="json",
        exclude={"evidence"},
    )
    payload["evidence"] = _canonical_evidence(domain.evidence)
    return payload


def _canonical_intent(intent: Intent) -> dict[str, Any]:
    payload = intent.model_dump(
        mode="json",
        exclude={"evidence"},
    )
    payload["evidence"] = _canonical_evidence(intent.evidence)
    return payload


def canonical_ruleset_payload(
    documents: LoadedRulesetDocuments,
) -> dict[str, Any]:
    """
    Return the logical ruleset representation used for integrity hashing.

    Physical YAML ordering is intentionally excluded from the identity.
    All semantically unordered collections are sorted by stable IDs.
    """
    validate_ruleset_semantics(documents)

    return {
        "schema_version": documents.config.schema_version,
        "ruleset_version": documents.profiles.ruleset_version,
        "router": documents.config.router.model_dump(mode="json"),
        "profiles": [
            profile.model_dump(mode="json")
            for profile in sorted(
                documents.profiles.profiles,
                key=lambda item: item.id,
            )
        ],
        "domains": [
            _canonical_domain(domain)
            for domain in sorted(
                documents.domains.domains,
                key=lambda item: item.id,
            )
        ],
        "intents": [
            _canonical_intent(intent)
            for intent in sorted(
                documents.intents.intents,
                key=lambda item: item.id,
            )
        ],
        "routes": [
            route.model_dump(mode="json")
            for route in sorted(
                documents.routing.routes,
                key=lambda item: item.id,
            )
        ],
    }


def canonical_ruleset_json(
    documents: LoadedRulesetDocuments,
) -> str:
    payload = canonical_ruleset_payload(documents)

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_ruleset_bytes(
    documents: LoadedRulesetDocuments,
) -> bytes:
    return canonical_ruleset_json(documents).encode("utf-8")


def compute_ruleset_hash(
    documents: LoadedRulesetDocuments,
) -> str:
    return hashlib.sha256(
        canonical_ruleset_bytes(documents)
    ).hexdigest()


def create_ruleset_snapshot(
    documents: LoadedRulesetDocuments,
) -> RulesetSnapshot:
    validate_ruleset_semantics(documents)

    domains = tuple(
        domain.model_copy(
            update={
                "evidence": tuple(
                    sorted(
                        domain.evidence,
                        key=lambda item: item.id,
                    )
                )
            }
        )
        for domain in sorted(
            documents.domains.domains,
            key=lambda item: item.id,
        )
    )

    intents = tuple(
        intent.model_copy(
            update={
                "evidence": tuple(
                    sorted(
                        intent.evidence,
                        key=lambda item: item.id,
                    )
                )
            }
        )
        for intent in sorted(
            documents.intents.intents,
            key=lambda item: item.id,
        )
    )

    return RulesetSnapshot(
        schema_version=documents.config.schema_version,
        ruleset_version=documents.profiles.ruleset_version,
        ruleset_hash=compute_ruleset_hash(documents),
        router=documents.config.router,
        profiles=tuple(
            sorted(
                documents.profiles.profiles,
                key=lambda item: item.id,
            )
        ),
        domains=domains,
        intents=intents,
        routes=tuple(
            sorted(
                documents.routing.routes,
                key=lambda item: item.id,
            )
        ),
    )
