from pathlib import Path

import pytest

from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.loader import (
    LoadedRulesetDocuments,
    load_ruleset_documents,
)
from villaz_router.models import (
    DomainsDocument,
    Evidence,
    Intent,
    IntentsDocument,
    Profile,
    ProfilesDocument,
    Route,
    RouteCondition,
    RouteResult,
    RoutingDocument,
)
from villaz_router.validation import validate_ruleset_semantics


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _official() -> LoadedRulesetDocuments:
    return load_ruleset_documents(PROJECT_ROOT)


def test_official_ruleset_is_semantically_valid() -> None:
    validate_ruleset_semantics(_official())


def test_duplicate_profile_id_is_invalid() -> None:
    documents = _official()

    invalid = documents.__class__(
        config=documents.config,
        profiles=ProfilesDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            profiles=(
                Profile(id="mobile-dev", enabled=True),
                Profile(id="mobile-dev", enabled=True),
            ),
        ),
        domains=documents.domains,
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError) as exc_info:
        validate_ruleset_semantics(invalid)

    assert exc_info.value.code is RouterErrorCode.INVALID_RULESET


def test_duplicate_evidence_id_is_invalid() -> None:
    documents = _official()

    duplicate = Evidence(
        id="DOMAIN-MOBILE-001",
        type="term",
        strength="strong",
        value="duplicado",
    )

    first_domain = documents.domains.domains[0]

    changed_domain = first_domain.model_copy(
        update={
            "evidence": first_domain.evidence + (duplicate,)
        }
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=DomainsDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            domains=(
                changed_domain,
                *documents.domains.domains[1:],
            ),
        ),
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_unknown_route_profile_is_invalid() -> None:
    documents = _official()

    route = Route(
        id="ROUTE-INVALID",
        enabled=True,
        priority=100,
        when=RouteCondition(domain="mobile"),
        result=RouteResult(profile="does-not-exist"),
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=RoutingDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            routes=(route,),
        ),
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_unknown_route_domain_is_invalid() -> None:
    documents = _official()

    route = Route(
        id="ROUTE-INVALID",
        enabled=True,
        priority=100,
        when=RouteCondition(domain="unknown"),
        result=RouteResult(profile="mobile-dev"),
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=RoutingDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            routes=(route,),
        ),
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_unknown_route_intent_is_invalid() -> None:
    documents = _official()

    route = Route(
        id="ROUTE-INVALID",
        enabled=True,
        priority=100,
        when=RouteCondition(intent="unknown"),
        result=RouteResult(profile="docs-dev"),
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=RoutingDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            routes=(route,),
        ),
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_non_route_capable_intent_cannot_be_used_by_route() -> None:
    documents = _official()

    route = Route(
        id="ROUTE-INVALID",
        enabled=True,
        priority=100,
        when=RouteCondition(intent="development"),
        result=RouteResult(profile="docs-dev"),
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=RoutingDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            routes=(route,),
        ),
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_ruleset_version_mismatch_is_invalid() -> None:
    documents = _official()

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=IntentsDocument(
            schema_version="1.0",
            ruleset_version="2.0.0",
            intents=documents.intents.intents,
        ),
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_profile_id_cannot_be_evidence_value() -> None:
    documents = _official()

    intent = Intent(
        id="invalid-intent",
        route_capable=False,
        evidence=(
            Evidence(
                id="INVALID-EVIDENCE-001",
                type="term",
                strength="strong",
                value="mobile-dev",
            ),
        ),
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=IntentsDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            intents=documents.intents.intents + (intent,),
        ),
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_duplicate_normalized_evidence_value_in_same_target_is_invalid() -> None:
    documents = _official()

    first_domain = documents.domains.domains[0]

    duplicate = Evidence(
        id="DOMAIN-MOBILE-999",
        type="term",
        strength="strong",
        value="  FLUTTER  ",
    )

    changed_domain = first_domain.model_copy(
        update={
            "evidence": first_domain.evidence + (duplicate,)
        }
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=DomainsDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            domains=(
                changed_domain,
                *documents.domains.domains[1:],
            ),
        ),
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)
