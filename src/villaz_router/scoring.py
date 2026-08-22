from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from villaz_router.config import ScoringConfig
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.models import (
    Evidence,
    EvidenceContribution,
    EvidenceMatch,
    EvidenceStrength,
    ScoringResult,
)


def _first_duplicate_id(ids: Iterable[str]) -> str | None:
    counts = Counter(ids)
    duplicates = sorted(
        evidence_id
        for evidence_id, count in counts.items()
        if count > 1
    )
    if not duplicates:
        return None
    return duplicates[0]


def _invalid_scoring_input(message: str) -> RouterError:
    return RouterError(
        RouterErrorCode.INVALID_SCORING_INPUT,
        message,
    )


def _weight_for_strength(
    strength: EvidenceStrength,
    scoring: ScoringConfig,
) -> int:
    if strength is EvidenceStrength.STRONG:
        return scoring.strong
    if strength is EvidenceStrength.MEDIUM:
        return scoring.medium
    return scoring.weak


def score_evidence_matches(
    matches: Iterable[EvidenceMatch],
    evidence_items: Iterable[Evidence],
    scoring: ScoringConfig,
) -> ScoringResult:
    match_items = tuple(matches)
    configured_evidence = tuple(evidence_items)

    duplicate_evidence_id = _first_duplicate_id(
        evidence.id
        for evidence in configured_evidence
    )
    if duplicate_evidence_id is not None:
        raise _invalid_scoring_input(
            f"duplicate evidence id: {duplicate_evidence_id}"
        )

    duplicate_match_id = _first_duplicate_id(
        match.evidence_id
        for match in match_items
    )
    if duplicate_match_id is not None:
        raise _invalid_scoring_input(
            f"duplicate evidence match id: {duplicate_match_id}"
        )

    evidence_by_id = {
        evidence.id: evidence
        for evidence in configured_evidence
    }

    unknown_ids = sorted(
        {
            match.evidence_id
            for match in match_items
            if match.evidence_id not in evidence_by_id
        }
    )
    if unknown_ids:
        raise _invalid_scoring_input(
            f"evidence match references unknown evidence_id: {unknown_ids[0]}"
        )

    type_mismatch_ids = sorted(
        match.evidence_id
        for match in match_items
        if match.evidence_type
        is not evidence_by_id[match.evidence_id].type
    )
    if type_mismatch_ids:
        raise _invalid_scoring_input(
            "evidence match type does not match configured evidence: "
            f"{type_mismatch_ids[0]}"
        )

    value_mismatch_ids = sorted(
        match.evidence_id
        for match in match_items
        if match.evidence_value
        != evidence_by_id[match.evidence_id].value
    )
    if value_mismatch_ids:
        raise _invalid_scoring_input(
            "evidence match value does not match configured evidence: "
            f"{value_mismatch_ids[0]}"
        )

    contributions = tuple(
        sorted(
            (
                EvidenceContribution(
                    evidence_id=match.evidence_id,
                    strength=evidence_by_id[
                        match.evidence_id
                    ].strength,
                    weight=_weight_for_strength(
                        evidence_by_id[
                            match.evidence_id
                        ].strength,
                        scoring,
                    ),
                )
                for match in match_items
            ),
            key=lambda contribution: contribution.evidence_id,
        )
    )

    score = sum(
        contribution.weight
        for contribution in contributions
    )

    return ScoringResult(
        score=score,
        contributions=contributions,
    )
