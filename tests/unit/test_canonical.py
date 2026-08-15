from dataclasses import replace
from pathlib import Path

from villaz_router.canonical import (
    canonical_ruleset_bytes,
    canonical_ruleset_json,
    compute_ruleset_hash,
    create_ruleset_snapshot,
)
from villaz_router.loader import (
    LoadedRulesetDocuments,
    load_ruleset_documents,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _official() -> LoadedRulesetDocuments:
    return load_ruleset_documents(PROJECT_ROOT)


def _reverse_logical_collections(
    documents: LoadedRulesetDocuments,
) -> LoadedRulesetDocuments:
    domains = documents.domains.model_copy(
        update={
            "domains": tuple(
                domain.model_copy(
                    update={
                        "evidence": tuple(
                            reversed(domain.evidence)
                        )
                    }
                )
                for domain in reversed(
                    documents.domains.domains
                )
            )
        }
    )

    intents = documents.intents.model_copy(
        update={
            "intents": tuple(
                intent.model_copy(
                    update={
                        "evidence": tuple(
                            reversed(intent.evidence)
                        )
                    }
                )
                for intent in reversed(
                    documents.intents.intents
                )
            )
        }
    )

    return replace(
        documents,
        profiles=documents.profiles.model_copy(
            update={
                "profiles": tuple(
                    reversed(
                        documents.profiles.profiles
                    )
                )
            }
        ),
        domains=domains,
        intents=intents,
        routing=documents.routing.model_copy(
            update={
                "routes": tuple(
                    reversed(
                        documents.routing.routes
                    )
                )
            }
        ),
    )


def test_canonical_json_is_compact_and_deterministic() -> None:
    canonical = canonical_ruleset_json(_official())

    assert "\n" not in canonical
    assert ": " not in canonical
    assert ", " not in canonical

    assert canonical == canonical_ruleset_json(_official())


def test_canonical_representation_is_utf8_not_ascii_escaped() -> None:
    canonical = canonical_ruleset_bytes(_official())

    decoded = canonical.decode("utf-8")

    assert "\\u00e7" not in decoded
    assert "tributação" in decoded


def test_physical_collection_order_does_not_change_hash() -> None:
    documents = _official()
    reordered = _reverse_logical_collections(documents)

    assert compute_ruleset_hash(
        documents
    ) == compute_ruleset_hash(reordered)


def test_semantic_router_config_change_changes_hash() -> None:
    documents = _official()

    changed_scoring = documents.config.router.scoring.model_copy(
        update={"strong": 11}
    )

    changed_router = documents.config.router.model_copy(
        update={"scoring": changed_scoring}
    )

    changed_config = documents.config.model_copy(
        update={"router": changed_router}
    )

    changed = replace(
        documents,
        config=changed_config,
    )

    assert compute_ruleset_hash(
        documents
    ) != compute_ruleset_hash(changed)


def test_semantic_evidence_change_changes_hash() -> None:
    documents = _official()

    first_domain = documents.domains.domains[0]
    first_evidence = first_domain.evidence[0]

    changed_evidence = first_evidence.model_copy(
        update={
            "value": f"{first_evidence.value}-changed"
        }
    )

    changed_domain = first_domain.model_copy(
        update={
            "evidence": (
                changed_evidence,
                *first_domain.evidence[1:],
            )
        }
    )

    changed_domains = documents.domains.model_copy(
        update={
            "domains": (
                changed_domain,
                *documents.domains.domains[1:],
            )
        }
    )

    changed = replace(
        documents,
        domains=changed_domains,
    )

    assert compute_ruleset_hash(
        documents
    ) != compute_ruleset_hash(changed)


def test_ruleset_hash_is_lowercase_sha256_hex() -> None:
    ruleset_hash = compute_ruleset_hash(_official())

    assert len(ruleset_hash) == 64
    assert ruleset_hash == ruleset_hash.lower()
    assert all(
        character in "0123456789abcdef"
        for character in ruleset_hash
    )


def test_snapshot_uses_canonical_logical_order() -> None:
    documents = _reverse_logical_collections(_official())

    snapshot = create_ruleset_snapshot(documents)

    assert tuple(
        profile.id
        for profile in snapshot.profiles
    ) == tuple(
        sorted(
            profile.id
            for profile in snapshot.profiles
        )
    )

    assert tuple(
        domain.id
        for domain in snapshot.domains
    ) == tuple(
        sorted(
            domain.id
            for domain in snapshot.domains
        )
    )

    assert tuple(
        intent.id
        for intent in snapshot.intents
    ) == tuple(
        sorted(
            intent.id
            for intent in snapshot.intents
        )
    )

    assert tuple(
        route.id
        for route in snapshot.routes
    ) == tuple(
        sorted(
            route.id
            for route in snapshot.routes
        )
    )


def test_snapshot_hash_matches_canonical_documents() -> None:
    documents = _official()

    snapshot = create_ruleset_snapshot(documents)

    assert snapshot.schema_version == "1.0"
    assert snapshot.ruleset_version == "1.0.0"
    assert snapshot.ruleset_hash == compute_ruleset_hash(
        documents
    )


def test_snapshot_contains_immutable_router_settings() -> None:
    documents = _official()

    snapshot = create_ruleset_snapshot(documents)

    assert snapshot.router == documents.config.router
    assert snapshot.router.scoring.strong == 10
    assert snapshot.router.eligibility.minimum_score == 10
    assert snapshot.router.lifecycle.ruleset_reload == "startup_only"


def test_snapshot_rejects_invalid_hash_format() -> None:
    import pytest
    from pydantic import ValidationError

    snapshot = create_ruleset_snapshot(_official())

    with pytest.raises(ValidationError):
        snapshot.model_copy(
            update={"ruleset_hash": "invalid"},
        ).__class__.model_validate(
            {
                **snapshot.model_dump(mode="python"),
                "ruleset_hash": "invalid",
            }
        )


def test_official_ruleset_hash_matches_checkpoint() -> None:
    assert compute_ruleset_hash(_official()) == (
        "ee57b50c8ff5f15476276610b6850c30509933e129a7a43062159348e0cbe575"
    )


def test_snapshot_is_identical_after_physical_reordering() -> None:
    documents = _official()
    reordered = _reverse_logical_collections(documents)

    assert create_ruleset_snapshot(documents) == create_ruleset_snapshot(reordered)
