from villaz_router.bootstrap import bootstrap_runtime
from villaz_router.bootstrap_errors import (
    ApplicationBootstrapError,
    ApplicationBootstrapErrorCode,
    BootstrapStage,
)
from villaz_router.bootstrap_models import RuntimeContext

from villaz_router.canonical import (
    canonical_ruleset_bytes,
    canonical_ruleset_json,
    canonical_ruleset_payload,
    compute_ruleset_hash,
    create_ruleset_snapshot,
)
from villaz_router.config import (
    RouterConfigDocument,
    RouterSettings,
    ScoringConfig,
)
from villaz_router.dispatcher import build_dispatch_plan
from villaz_router.dispatcher_errors import DispatcherError, DispatcherErrorCode
from villaz_router.dispatcher_models import DispatchPlan
from villaz_router.errors import RouterError, RouterErrorCode
from villaz_router.matcher import match_evidence, match_evidence_set
from villaz_router.registry_canonical import (
    canonical_registry_bytes,
    canonical_registry_json,
    canonical_registry_payload,
    compute_registry_hash,
    create_profile_registry_snapshot,
)
from villaz_router.registry_errors import RegistryError, RegistryErrorCode
from villaz_router.registry_loader import load_profile_registry_snapshot
from villaz_router.registry_models import (
    ProfileDefinition,
    ProfileRegistrySnapshot,
)
from villaz_router.loader import (
    LoadedRulesetDocuments,
    load_and_validate_ruleset_documents,
    load_ruleset_documents,
    load_ruleset_snapshot,
)
from villaz_router.models import (
    Domain,
    DomainsDocument,
    Evidence,
    EvidenceContribution,
    EvidenceMatch,
    EvidenceStrength,
    EvidenceType,
    Intent,
    IntentsDocument,
    Profile,
    ProfilesDocument,
    Route,
    RouteCandidate,
    RouteCondition,
    RouteDecision,
    RouteRequest,
    RouteResult,
    RouteState,
    RoutingDocument,
    RoutingMode,
    RoutingReason,
    RulesetSnapshot,
    ScoringResult,
)
from villaz_router.normalization import normalize_text
from villaz_router.router import decide_route
from villaz_router.runtime_compatibility import validate_runtime_compatibility
from villaz_router.runtime_compatibility_errors import (
    RuntimeCompatibilityError,
    RuntimeCompatibilityErrorCode,
    RuntimeCompatibilityReason,
)
from villaz_router.scoring import score_evidence_matches
from villaz_router.validation import validate_ruleset_semantics

__all__ = [
    "ApplicationBootstrapError",
    "ApplicationBootstrapErrorCode",
    "BootstrapStage",
    "RuntimeContext",
    "bootstrap_runtime",
    "canonical_ruleset_bytes",
    "canonical_ruleset_json",
    "canonical_ruleset_payload",
    "canonical_registry_bytes",
    "canonical_registry_json",
    "canonical_registry_payload",
    "compute_registry_hash",
    "create_profile_registry_snapshot",
    "compute_ruleset_hash",
    "build_dispatch_plan",
    "DispatcherError",
    "DispatcherErrorCode",
    "DispatchPlan",
    "decide_route",
    "create_ruleset_snapshot",
    "Domain",
    "DomainsDocument",
    "Evidence",
    "EvidenceContribution",
    "EvidenceMatch",
    "EvidenceStrength",
    "EvidenceType",
    "Intent",
    "IntentsDocument",
    "LoadedRulesetDocuments",
    "Profile",
    "ProfileDefinition",
    "ProfileRegistrySnapshot",
    "ProfilesDocument",
    "Route",
    "RouteCandidate",
    "RouteCondition",
    "RouteDecision",
    "RouteRequest",
    "RouteResult",
    "RouteState",
    "RouterConfigDocument",
    "RouterError",
    "RouterErrorCode",
    "RegistryError",
    "RegistryErrorCode",
    "RouterSettings",
    "ScoringConfig",
    "RoutingDocument",
    "RoutingMode",
    "RoutingReason",
    "RulesetSnapshot",
    "ScoringResult",
    "load_and_validate_ruleset_documents",
    "match_evidence",
    "match_evidence_set",
    "normalize_text",
    "score_evidence_matches",
    "load_ruleset_documents",
    "load_ruleset_snapshot",
    "load_profile_registry_snapshot",
    "RuntimeCompatibilityError",
    "RuntimeCompatibilityErrorCode",
    "RuntimeCompatibilityReason",
    "validate_runtime_compatibility",
    "validate_ruleset_semantics",
]
