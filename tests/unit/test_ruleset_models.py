import pytest
from pydantic import ValidationError

from villaz_router.config import RouterConfigDocument
from villaz_router.models import (
    Domain,
    Evidence,
    EvidenceStrength,
    EvidenceType,
    Intent,
    Profile,
    Route,
    RouteCondition,
    RouteResult,
)


def test_evidence_accepts_normative_values() -> None:
    evidence = Evidence(
        id="DOMAIN-MOBILE-001",
        type=EvidenceType.TERM,
        strength=EvidenceStrength.STRONG,
        value="flutter",
    )

    assert evidence.id == "DOMAIN-MOBILE-001"
    assert evidence.value == "flutter"


def test_evidence_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            id="X",
            type="regex",
            strength="strong",
            value="flutter",
        )


def test_evidence_rejects_unknown_strength() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            id="X",
            type="term",
            strength="critical",
            value="flutter",
        )


def test_profile_is_immutable() -> None:
    profile = Profile(
        id="mobile-dev",
        enabled=True,
    )

    with pytest.raises(ValidationError):
        profile.enabled = False


def test_domain_contains_evidence() -> None:
    domain = Domain(
        id="mobile",
        evidence=(
            Evidence(
                id="DOMAIN-MOBILE-001",
                type="term",
                strength="strong",
                value="flutter",
            ),
        ),
    )

    assert len(domain.evidence) == 1


def test_intent_can_be_auxiliary() -> None:
    intent = Intent(
        id="development",
        route_capable=False,
        evidence=(
            Evidence(
                id="INTENT-DEV-001",
                type="term",
                strength="strong",
                value="implemente",
            ),
        ),
    )

    assert intent.route_capable is False


def test_route_accepts_intent_condition() -> None:
    route = Route(
        id="ROUTE-DOC-001",
        enabled=True,
        priority=400,
        when=RouteCondition(
            intent="documentation",
        ),
        result=RouteResult(
            profile="docs-dev",
        ),
    )

    assert route.when.intent == "documentation"
    assert route.when.domain is None


def test_route_accepts_domain_condition() -> None:
    route = Route(
        id="ROUTE-UNITY-001",
        enabled=True,
        priority=300,
        when=RouteCondition(
            domain="unity",
        ),
        result=RouteResult(
            profile="unity-dev",
        ),
    )

    assert route.when.domain == "unity"


def test_route_accepts_intent_and_domain_condition() -> None:
    condition = RouteCondition(
        intent="documentation",
        domain="mobile",
    )

    assert condition.intent == "documentation"
    assert condition.domain == "mobile"


def test_route_rejects_empty_condition() -> None:
    with pytest.raises(ValidationError):
        RouteCondition()


def test_router_config_matches_normative_structure() -> None:
    config = RouterConfigDocument.model_validate(
        {
            "schema_version": "1.0",
            "router": {
                "engine": {
                    "expected_major_version": 1,
                },
                "scoring": {
                    "strong": 10,
                    "medium": 4,
                    "weak": 1,
                },
                "eligibility": {
                    "minimum_score": 10,
                    "weak_only_cannot_qualify": True,
                },
                "ambiguity": {
                    "minimum_margin": 5,
                },
                "normalization": {
                    "unicode_nfkc": True,
                    "lowercase": True,
                    "lowercase_locale_independent": True,
                    "collapse_whitespace": True,
                    "accent_insensitive_matching": True,
                },
                "lifecycle": {
                    "ruleset_reload": "startup_only",
                    "immutable_snapshot_per_instance": True,
                },
                "integrity": {
                    "algorithm": "sha256",
                    "canonical_format": "deterministic_json_utf8",
                },
                "privacy": {
                    "store_full_message": False,
                    "store_evidence": True,
                },
            },
        }
    )

    assert config.router.scoring.strong == 10
    assert config.router.eligibility.minimum_score == 10
    assert config.router.ambiguity.minimum_margin == 5
