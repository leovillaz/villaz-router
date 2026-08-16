from __future__ import annotations

from collections.abc import Iterable

from villaz_router.models import Evidence, EvidenceMatch, EvidenceType
from villaz_router.normalization import normalize_text


def _is_word_char(char: str) -> bool:
    return char == "_" or char.isalnum()


def _has_term_boundaries(
    text: str,
    *,
    start: int,
    end: int,
) -> bool:
    left_ok = start == 0 or not _is_word_char(text[start - 1])
    right_ok = end == len(text) or not _is_word_char(text[end])
    return left_ok and right_ok


def _find_phrase(
    normalized_message: str,
    normalized_value: str,
) -> tuple[int, int] | None:
    start = normalized_message.find(normalized_value)
    if start < 0:
        return None
    return start, start + len(normalized_value)


def _find_term(
    normalized_message: str,
    normalized_value: str,
) -> tuple[int, int] | None:
    search_from = 0

    while True:
        start = normalized_message.find(
            normalized_value,
            search_from,
        )
        if start < 0:
            return None

        end = start + len(normalized_value)
        if _has_term_boundaries(
            normalized_message,
            start=start,
            end=end,
        ):
            return start, end

        search_from = start + 1


def match_evidence(
    normalized_message: str,
    evidence: Evidence,
) -> EvidenceMatch | None:
    normalized_value = normalize_text(evidence.value)

    if not normalized_message or not normalized_value:
        return None

    if evidence.type is EvidenceType.PHRASE:
        span = _find_phrase(
            normalized_message,
            normalized_value,
        )
    else:
        span = _find_term(
            normalized_message,
            normalized_value,
        )

    if span is None:
        return None

    start, end = span

    return EvidenceMatch(
        evidence_id=evidence.id,
        evidence_type=evidence.type,
        evidence_value=evidence.value,
        start=start,
        end=end,
    )


def match_evidence_set(
    normalized_message: str,
    evidence_items: Iterable[Evidence],
) -> tuple[EvidenceMatch, ...]:
    matches = tuple(
        match
        for evidence in evidence_items
        if (match := match_evidence(normalized_message, evidence))
        is not None
    )

    return tuple(
        sorted(
            matches,
            key=lambda match: match.evidence_id,
        )
    )
