from collections.abc import Iterable
import re
import unicodedata

from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.loader import LoadedRulesetDocuments
from villaz_router.models import Domain, Evidence, Intent


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
)
_SCHEMA_VERSION_PATTERN = re.compile(r"^[0-9]+[.][0-9]+$")
_RULESET_VERSION_PATTERN = re.compile(
    r"^[0-9]+[.][0-9]+[.][0-9]+$"
)


def _invalid(message: str) -> RouterError:
    return RouterError(
        RouterErrorCode.INVALID_RULESET,
        message,
    )


def _require_unique_ids(
    items: Iterable[object],
    *,
    label: str,
) -> None:
    seen: set[str] = set()

    for item in items:
        item_id = getattr(item, "id")

        if item_id in seen:
            raise _invalid(
                f"duplicate {label} id: {item_id}"
            )

        seen.add(item_id)


def _validate_identifiers(
    items: Iterable[object],
    *,
    label: str,
) -> None:
    for item in items:
        item_id = getattr(item, "id")

        if not _IDENTIFIER_PATTERN.fullmatch(item_id):
            raise _invalid(
                f"invalid {label} id: {item_id!r}"
            )


def _validate_versions(
    documents: LoadedRulesetDocuments,
) -> None:
    versions = {
        documents.profiles.ruleset_version,
        documents.domains.ruleset_version,
        documents.intents.ruleset_version,
        documents.routing.ruleset_version,
    }

    if len(versions) != 1:
        raise _invalid(
            "ruleset_version mismatch between ruleset documents"
        )

    ruleset_version = next(iter(versions))

    if not _RULESET_VERSION_PATTERN.fullmatch(ruleset_version):
        raise _invalid(
            f"invalid ruleset_version: {ruleset_version}"
        )

    major_version = int(ruleset_version.split(".", 1)[0])

    expected_major = (
        documents.config.router.engine.expected_major_version
    )

    if major_version != expected_major:
        raise _invalid(
            "ruleset major version is incompatible with router engine"
        )


def _validate_schema_versions(
    documents: LoadedRulesetDocuments,
) -> None:
    schema_versions = {
        documents.config.schema_version,
        documents.profiles.schema_version,
        documents.domains.schema_version,
        documents.intents.schema_version,
        documents.routing.schema_version,
    }

    if len(schema_versions) != 1:
        raise _invalid(
            "schema_version mismatch between ruleset documents"
        )

    schema_version = next(iter(schema_versions))

    if not _SCHEMA_VERSION_PATTERN.fullmatch(schema_version):
        raise _invalid(
            f"invalid schema_version: {schema_version}"
        )


def _validate_router_config(
    documents: LoadedRulesetDocuments,
) -> None:
    scoring = documents.config.router.scoring

    if not (scoring.strong > scoring.medium > scoring.weak):
        raise _invalid(
            "scoring must satisfy strong > medium > weak"
        )


def _iter_all_evidence(
    domains: tuple[Domain, ...],
    intents: tuple[Intent, ...],
) -> Iterable[Evidence]:
    for domain in domains:
        yield from domain.evidence

    for intent in intents:
        yield from intent.evidence


def _validate_evidence(
    documents: LoadedRulesetDocuments,
) -> None:
    all_evidence = tuple(
        _iter_all_evidence(
            documents.domains.domains,
            documents.intents.intents,
        )
    )

    _require_unique_ids(
        all_evidence,
        label="evidence",
    )

    profile_ids = {
        profile.id
        for profile in documents.profiles.profiles
    }

    for evidence in all_evidence:
        if not evidence.value.strip():
            raise _invalid(
                f"evidence value cannot be empty: {evidence.id}"
            )

        normalized_value = evidence.value.strip().casefold()

        normalized_profile_ids = {
            profile_id.casefold()
            for profile_id in profile_ids
        }

        if normalized_value in normalized_profile_ids:
            raise _invalid(
                "profile id cannot be used as evidence value: "
                f"{evidence.id}"
            )


def _validate_duplicate_evidence_values_per_target(
    documents: LoadedRulesetDocuments,
) -> None:
    def validate_target(
        target_id: str,
        evidence_items: tuple[Evidence, ...],
    ) -> None:
        seen: set[str] = set()

        for evidence in evidence_items:
            normalized = unicodedata.normalize(
                "NFKD",
                unicodedata.normalize(
                    "NFKC",
                    evidence.value,
                ).casefold(),
            )
            normalized = "".join(
                char
                for char in normalized
                if not unicodedata.combining(char)
            )
            normalized = " ".join(normalized.split())

            if normalized in seen:
                raise _invalid(
                    "duplicate normalized evidence value in "
                    f"{target_id}: {evidence.value}"
                )

            seen.add(normalized)

    for domain in documents.domains.domains:
        validate_target(
            domain.id,
            domain.evidence,
        )

    for intent in documents.intents.intents:
        validate_target(
            intent.id,
            intent.evidence,
        )


def _validate_routes(
    documents: LoadedRulesetDocuments,
) -> None:
    profiles = {
        profile.id: profile
        for profile in documents.profiles.profiles
    }

    domains = {
        domain.id: domain
        for domain in documents.domains.domains
    }

    intents = {
        intent.id: intent
        for intent in documents.intents.intents
    }

    for route in documents.routing.routes:
        profile = profiles.get(route.result.profile)

        if profile is None:
            raise _invalid(
                f"route references unknown profile: {route.id}"
            )

        if route.enabled and not profile.enabled:
            raise _invalid(
                f"enabled route references disabled profile: {route.id}"
            )

        if route.when.domain is not None:
            if route.when.domain not in domains:
                raise _invalid(
                    f"route references unknown domain: {route.id}"
                )

        if route.when.intent is not None:
            intent = intents.get(route.when.intent)

            if intent is None:
                raise _invalid(
                    f"route references unknown intent: {route.id}"
                )

            if not intent.route_capable:
                raise _invalid(
                    "route references non-route-capable intent: "
                    f"{route.id}"
                )


def validate_ruleset_semantics(
    documents: LoadedRulesetDocuments,
) -> None:
    _validate_schema_versions(documents)
    _validate_versions(documents)
    _validate_router_config(documents)

    _require_unique_ids(
        documents.profiles.profiles,
        label="profile",
    )
    _validate_identifiers(
        documents.profiles.profiles,
        label="profile",
    )

    _require_unique_ids(
        documents.domains.domains,
        label="domain",
    )
    _validate_identifiers(
        documents.domains.domains,
        label="domain",
    )

    _require_unique_ids(
        documents.intents.intents,
        label="intent",
    )
    _validate_identifiers(
        documents.intents.intents,
        label="intent",
    )

    _require_unique_ids(
        documents.routing.routes,
        label="route",
    )
    _validate_identifiers(
        documents.routing.routes,
        label="route",
    )

    _validate_evidence(documents)
    _validate_duplicate_evidence_values_per_target(documents)
    _validate_routes(documents)
