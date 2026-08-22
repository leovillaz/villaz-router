from villaz_router.config import EligibilityConfig
from villaz_router.models import EvidenceStrength, ScoringResult


def _is_scoring_result_eligible(
    result: ScoringResult,
    config: EligibilityConfig,
) -> bool:
    if result.score < config.minimum_score:
        return False

    if not config.weak_only_cannot_qualify:
        return True

    if not result.contributions:
        return False

    return any(
        contribution.strength is not EvidenceStrength.WEAK
        for contribution in result.contributions
    )
