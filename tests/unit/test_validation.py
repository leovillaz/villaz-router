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


def test_security_route_uses_review_security_intent() -> None:
    documents = _official()

    route = next(
        item
        for item in documents.routing.routes
        if item.id == "ROUTE-REVIEW-001"
    )

    assert route.when.intent == "review-security"
    assert route.when.domain is None
    assert route.result.profile == "code-review-security"


def test_enabled_route_to_disabled_profile_is_invalid() -> None:
    documents = _official()

    profiles = tuple(
        profile.model_copy(update={"enabled": False})
        if profile.id == "code-review-security"
        else profile
        for profile in documents.profiles.profiles
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=ProfilesDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            profiles=profiles,
        ),
        domains=documents.domains,
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_duplicate_enabled_route_priority_is_valid() -> None:
    documents = _official()

    duplicate = documents.routing.routes[0].model_copy(
        update={"id": "ROUTE-DUPLICATE-PRIORITY"}
    )

    valid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=RoutingDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            routes=documents.routing.routes + (duplicate,),
        ),
    )

    validate_ruleset_semantics(valid)


def test_invalid_identifier_is_rejected() -> None:
    documents = _official()

    invalid = documents.__class__(
        config=documents.config,
        profiles=ProfilesDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            profiles=(
                Profile(id=" invalid-profile", enabled=True),
            ),
        ),
        domains=documents.domains,
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_accent_folded_duplicate_evidence_is_invalid() -> None:
    documents = _official()

    fiscal = next(
        domain
        for domain in documents.domains.domains
        if domain.id == "fiscal"
    )

    duplicate = Evidence(
        id="DOMAIN-FISCAL-999",
        type="term",
        strength="strong",
        value="tributacao",
    )

    changed = fiscal.model_copy(
        update={"evidence": fiscal.evidence + (duplicate,)}
    )

    domains = tuple(
        changed if domain.id == "fiscal" else domain
        for domain in documents.domains.domains
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=DomainsDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            domains=domains,
        ),
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)


def test_minimum_score_may_exceed_strong_evidence_score() -> None:
    documents = _official()

    scoring = documents.config.router.scoring

    eligibility = documents.config.router.eligibility.model_copy(
        update={"minimum_score": scoring.strong + 5}
    )
    router = documents.config.router.model_copy(
        update={"eligibility": eligibility}
    )
    config = documents.config.model_copy(
        update={"router": router}
    )

    valid = documents.__class__(
        config=config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=documents.routing,
    )

    validate_ruleset_semantics(valid)


def test_invalid_scoring_order_is_rejected() -> None:
    documents = _official()

    scoring = documents.config.router.scoring.model_copy(
        update={"strong": 1, "medium": 4, "weak": 1}
    )
    router = documents.config.router.model_copy(
        update={"scoring": scoring}
    )
    config = documents.config.model_copy(
        update={"router": router}
    )

    invalid = documents.__class__(
        config=config,
        profiles=documents.profiles,
        domains=documents.domains,
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)



def test_evidence_that_normalizes_to_empty_is_invalid() -> None:
    documents = _official()

    mobile = next(
        domain
        for domain in documents.domains.domains
        if domain.id == "mobile"
    )

    invalid_evidence = Evidence(
        id="DOMAIN-MOBILE-999",
        type="term",
        strength="strong",
        value="\u0301",
    )

    changed = mobile.model_copy(
        update={"evidence": mobile.evidence + (invalid_evidence,)}
    )

    domains = tuple(
        changed if domain.id == "mobile" else domain
        for domain in documents.domains.domains
    )

    invalid = documents.__class__(
        config=documents.config,
        profiles=documents.profiles,
        domains=DomainsDocument(
            schema_version="1.0",
            ruleset_version="1.0.0",
            domains=domains,
        ),
        intents=documents.intents,
        routing=documents.routing,
    )

    with pytest.raises(RouterError):
        validate_ruleset_semantics(invalid)
