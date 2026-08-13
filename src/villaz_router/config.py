from enum import StrEnum

from pydantic import BaseModel, ConfigDict, PositiveInt


class RulesetReloadMode(StrEnum):
    STARTUP_ONLY = "startup_only"


class IntegrityAlgorithm(StrEnum):
    SHA256 = "sha256"


class CanonicalFormat(StrEnum):
    DETERMINISTIC_JSON_UTF8 = "deterministic_json_utf8"


class StrictFrozenModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EngineConfig(StrictFrozenModel):
    expected_major_version: PositiveInt


class ScoringConfig(StrictFrozenModel):
    strong: PositiveInt
    medium: PositiveInt
    weak: PositiveInt


class EligibilityConfig(StrictFrozenModel):
    minimum_score: PositiveInt
    weak_only_cannot_qualify: bool


class AmbiguityConfig(StrictFrozenModel):
    minimum_margin: PositiveInt


class NormalizationConfig(StrictFrozenModel):
    unicode_nfkc: bool
    lowercase: bool
    lowercase_locale_independent: bool
    collapse_whitespace: bool
    accent_insensitive_matching: bool


class LifecycleConfig(StrictFrozenModel):
    ruleset_reload: RulesetReloadMode
    immutable_snapshot_per_instance: bool


class IntegrityConfig(StrictFrozenModel):
    algorithm: IntegrityAlgorithm
    canonical_format: CanonicalFormat


class PrivacyConfig(StrictFrozenModel):
    store_full_message: bool
    store_evidence: bool


class RouterSettings(StrictFrozenModel):
    engine: EngineConfig
    scoring: ScoringConfig
    eligibility: EligibilityConfig
    ambiguity: AmbiguityConfig
    normalization: NormalizationConfig
    lifecycle: LifecycleConfig
    integrity: IntegrityConfig
    privacy: PrivacyConfig


class RouterConfigDocument(StrictFrozenModel):
    schema_version: str
    router: RouterSettings
