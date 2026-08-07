"""Pydantic config schemas + loaders.

Configs are pre-registered (git-tagged `prereg-v1`) BEFORE any results exist.
Every runtime read goes through these models so typos fail loud.

Files loaded from `configs/`:
    providers.yaml   — 6 providers × endpoints × env keys (per-use-case model
                       lives in voices.yaml, per spec §3.2)
    voices.yaml      — locked voice AND model per provider × use case + reasoning
    gates.yaml       — per-use-case gates + measurement/acoustic noise-floor rules
                       + WER threshold + hygiene thresholds
    analyzers.yaml   — TTSDS2 reference + noise reference + Audiobox axes
                       + judge revisions + WER normaliser + MDD statement
    pricing.yaml     — published rates per provider, date-stamped per cell

Files loaded from `corpus/`:
    conversational.yaml, narration.yaml — 60 novel + 15 probe = 75 items
    variance_subset.yaml                — 10 items per use case, frozen in prereg
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

UseCase = Literal["conversational", "narration"]
Stratum = Literal["short", "medium", "long", "jargon", "edge", "probe"]

# Audiobox Aesthetics produces four axes per clip; which ones we REPORT is
# pre-committed in analyzers.yaml (spec B.2 — reporting all four unlabelled
# would invite post-hoc selection).
AudioboxAxis = Literal[
    "content_enjoyment",
    "content_usefulness",
    "production_complexity",
    "production_quality",
]

NaPolicy = Literal["exempt-and-annotate", "exclude-from-use-case", "fail"]


# --- providers.yaml --------------------------------------------------------


class ProviderConfig(BaseModel):
    """One provider entry in providers.yaml.

    Note: `model` moved to voices.yaml per spec §3.2 — recommended model is
    per (provider, use_case), not per provider. providers.yaml carries the
    stable identity (name, env key, endpoint).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Short key used in paths and CLI: `deepgram`, `elevenlabs`...")
    display_name: str = Field(description="Human-readable: `Deepgram Aura-2`")
    endpoint: str | None = Field(
        default=None, description="Base URL override; adapter default if None"
    )
    env_key: str = Field(description="Env var holding the API key, e.g. `DEEPGRAM_API_KEY`")
    tier: Literal["core", "control", "stretch"] = "core"
    notes: str = ""


class ProvidersFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: list[ProviderConfig]

    def by_name(self, name: str) -> ProviderConfig:
        for p in self.providers:
            if p.name == name:
                return p
        raise KeyError(f"Provider `{name}` not in providers.yaml")


# --- voices.yaml -----------------------------------------------------------


class VoiceSelection(BaseModel):
    """One voice + model locked for one provider × use case (spec §3.2).

    `model` is here (not in providers.yaml) because several providers ship a
    low-latency model and a high-quality model, and a buyer would deploy the
    former for a support agent and the latter for narration. Generation "at
    the highest quality tier" would make latency leaders fail the
    conversational gate by construction of our own protocol — that was
    defect 3.37.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str
    use_case: UseCase
    voice_id: str
    model: str = Field(description="Provider's recommended model string for this use case")
    reasoning: str = Field(description="One line: why this voice + model for this use case")
    split_model_from_quality: bool = Field(
        default=False,
        description=(
            "True when this (provider, use_case) uses a DIFFERENT model for "
            "quality/WER vs latency (e.g. Fish free tier for quality, paid for "
            "latency). Requires an on-chart annotation per defect 3.38."
        ),
    )
    quality_model: str | None = Field(
        default=None,
        description=(
            "If split_model_from_quality=True, the model string used for "
            "quality/WER runs. `model` is then the LATENCY model string."
        ),
    )

    @model_validator(mode="after")
    def _validate_split(self) -> VoiceSelection:
        if self.split_model_from_quality and self.quality_model is None:
            raise ValueError(
                f"{self.provider}×{self.use_case}: split_model_from_quality=True "
                "requires quality_model to be set"
            )
        if self.quality_model is not None and not self.split_model_from_quality:
            raise ValueError(
                f"{self.provider}×{self.use_case}: quality_model set but "
                "split_model_from_quality=False — pick one"
            )
        return self


class VoicesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voices: list[VoiceSelection]

    def get(self, provider: str, use_case: UseCase) -> VoiceSelection:
        for v in self.voices:
            if v.provider == provider and v.use_case == use_case:
                return v
        raise KeyError(f"No voice locked for {provider} × {use_case}")


# --- gates.yaml ------------------------------------------------------------


class Gate(BaseModel):
    """One hard gate for one use case.

    v2 additions (spec §5): `na_policy` for structurally unmeasurable inputs
    (defect 3.22); `robustness_points` explicit list instead of blanket ±20%
    (defect 3.40).
    """

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(description="e.g. `ttfa_p90_ms`, `rtf`, `clipped_samples`")
    op: Literal["lt", "lte", "gt", "gte", "eq"]
    threshold: float
    rationale: str = Field(description="One sentence: why this gate exists")
    na_policy: NaPolicy = Field(
        default="exempt-and-annotate",
        description=(
            "How to treat systems where this metric is structurally unmeasurable "
            "(e.g. Orpheus latency). Default: exempt-and-annotate keeps the "
            "system in the use case with a 'not assessed — reason' status."
        ),
    )
    robustness_points: list[float] = Field(
        default_factory=list,
        description=(
            "Explicit list of alternate thresholds for the robustness sweep. "
            "Replaces the blanket ±20% (spec §5). For the conversational "
            "latency gate: [300, 400, 500, 600] to actually reach the "
            "500-600ms perception threshold the rationale cites."
        ),
    )


class UseCaseGates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: UseCase
    gates: list[Gate]


class MeasurementNoiseFloor(BaseModel):
    """The v2 measurement-noise-floor rule (spec §3.4, defect 3.19).

    The 2× per-generation SD rule from an earlier draft was wrong by ~17×:
    it would have suppressed essentially every real difference. Correct rule:
    a between-provider difference counts as a difference only when it exceeds
    `z_multiplier × SE(difference)`, where SE(difference) is the measured
    within-provider SD divided by √(item count).

    Applied ONLY to the two metrics where variance is measured (TTSDS2, item
    WER). Reported per provider, not pooled — pooling would export a noisy
    provider's variance onto everyone else's comparisons.
    """

    model_config = ConfigDict(extra="forbid")

    z_multiplier: float = Field(
        default=1.96,
        description="1.96 = 95% CI on the difference of aggregates",
    )
    metrics: list[str] = Field(
        default_factory=lambda: ["ttsds2", "item_wer"],
        description="Metrics with repeat-draw variance; rule scope cannot drift",
    )
    per_provider: bool = Field(
        default=True,
        description="True (per-provider) NOT pooled — spec §3.4",
    )
    rationale: str = Field(description="Why this z_multiplier + scope")


class WerBandCutpoints(BaseModel):
    """WER band definitions (A/B/C...) pre-committed in gates.yaml.

    Spec §A.2: "the band is a published column and 'A / B / C' without stated
    boundaries is not a measurement." Each band applies to the two-judge
    `agreement_error_rate`, not raw single-judge WER.
    """

    model_config = ConfigDict(extra="forbid")

    A_max: float = Field(description="Agreement error rate ≤ this = band A")
    B_max: float = Field(description="Agreement error rate ≤ this = band B")
    # everything above B_max = band C


class WerFailureRule(BaseModel):
    """Per-item WER failure — spec §A.2 (defect 3.24).

    An item counts as a failure when EITHER:
      - agreement_error_rate exceeds `agreement_error_rate_threshold`, OR
      - any agreed deletion/substitution falls inside a numeric, currency
        or date span (the "one mangled dollar amount matters more than
        five wrong function words" clause).
    """

    model_config = ConfigDict(extra="forbid")

    agreement_error_rate_threshold: float = Field(
        default=0.05,
        description="Per-item agreement error rate above this = failure",
    )
    span_hard_fail: bool = Field(
        default=True,
        description=(
            "True: any agreed error inside a numeric/currency/date span is "
            "an automatic failure, regardless of overall rate"
        ),
    )
    span_types: list[str] = Field(
        default_factory=lambda: ["numeric", "currency", "date"],
        description="Which spans trigger the hard-fail clause",
    )
    rationale: str = ""


class CatastrophicEventDetectors(BaseModel):
    """Detector thresholds for the four typed event counts (spec §A.2)."""

    model_config = ConfigDict(extra="forbid")

    truncation_duration_ratio_lt: float = Field(
        default=0.60,
        description=(
            "Decoded duration below this fraction of predicted-from-char-count "
            "= truncation event"
        ),
    )
    repetition_loop_ngram: int = Field(
        default=4,
        description="n-gram size for repetition loop detection",
    )
    repetition_loop_min_repeats: int = Field(
        default=3,
        description="Consecutive repeats of the same n-gram in BOTH transcripts",
    )
    word_drop_min_run: int = Field(
        default=2,
        description="Agreed deletion run of ≥ this many tokens = drop event",
    )
    hallucination_min_run: int = Field(
        default=3,
        description="Agreed insertion run of ≥ this many tokens = hallucination",
    )


class HygieneThresholds(BaseModel):
    """Hygiene thresholds — pre-committed alongside gates (spec §5).

    Renamed from `noise_floor_dbfs_max` (defect 3.39): "noise floor" was
    ambiguous in adjacent config rows — statistical variance versus acoustic
    dBFS. The acoustic one lives here.
    """

    model_config = ConfigDict(extra="forbid")

    acoustic_noise_floor_dbfs_max: float = Field(
        default=-40.0,
        description="dBFS floor above which audio is audibly hissy (spec A.5)",
    )
    max_clipped_samples: int = Field(
        default=0,
        description="Waveform clipping is unfixable downstream",
    )
    rationale: str = ""


class GatesFile(BaseModel):
    """gates.yaml — gates + noise-floor rules + WER threshold + WER band cutpoints
    + catastrophic-event detector thresholds + hygiene."""

    model_config = ConfigDict(extra="forbid")

    use_cases: list[UseCaseGates]
    measurement_noise_floor: MeasurementNoiseFloor
    wer_bands: WerBandCutpoints
    wer_failure: WerFailureRule
    catastrophic_events: CatastrophicEventDetectors
    hygiene: HygieneThresholds


# --- analyzers.yaml (expanded in v2) ---------------------------------------


class TtsdsReferenceSet(BaseModel):
    """Per-use-case TTSDS2 reference (spec §A.3, R3)."""

    model_config = ConfigDict(extra="forbid")

    use_case: UseCase
    dataset_id: str = Field(description="Reference dataset identifier (HF, name, or path)")
    rationale: str = Field(description="One line: why this reference matches the use case domain")


class TtsdsNoiseReference(BaseModel):
    """TTSDS2 also needs a NOISE reference in addition to speech (spec §A.3
    line 852: "The reference is two corpora, not one")."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    rationale: str


class JudgeRevision(BaseModel):
    """One ASR judge with a pinned model revision (spec §4.2)."""

    model_config = ConfigDict(extra="forbid")

    name: Literal["parakeet", "faster-whisper"] = Field(
        description="Judge identity; the two must remain independent per spec §4.2"
    )
    loader: Literal["transformers", "ctranslate2"]
    model_id: str = Field(
        description=(
            "HF model id. For Parakeet: RNNT variant (`nvidia/parakeet-rnnt-*`) — "
            "TDT is not in a released `transformers` version yet (spec B.3, "
            "verified 2026-08-06). Phase B re-checks."
        )
    )
    revision: str = Field(
        description="Commit SHA or tag for reproducibility; NEVER 'main' or 'latest'",
    )


class MddEstimate(BaseModel):
    """Pre-registered minimum-detectable-difference power statement (spec §4.3,
    defect 3.21)."""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(
        default="TODO_choose_before_phase_D",
        description="e.g. 'simulated BT with clustered bootstrap'",
    )
    n_judgments_target: int = Field(default=210)
    n_judgments_minimum: int = Field(default=126)
    mdd_at_target: float | None = Field(
        default=None,
        description="Estimated MDD at n_judgments_target (fill in after simulation)",
    )
    mdd_at_minimum: float | None = Field(
        default=None,
        description="Estimated MDD at n_judgments_minimum",
    )
    rationale: str = ""


class BootstrapSpec(BaseModel):
    """D4 bootstrap configuration (spec §4.3, defect 3.20)."""

    model_config = ConfigDict(extra="forbid")

    resamples: int = Field(default=2000)
    cluster_by: Literal["item", "session", "none"] = Field(
        default="item",
        description=(
            "Clustered bootstrap; independent resampling ignores clustering "
            "by item/session and understates intervals"
        ),
    )
    penalty_term: float = Field(
        default=0.5,
        description="Small penalty in BT fit to keep all-win/all-loss resamples finite",
    )


class AnalyzersFile(BaseModel):
    """analyzers.yaml — pinned analyzer parameters (spec §4.3, A.3, B.3).

    v2: adds noise reference (defect 3.9), Audiobox axes pre-commit
    (defect 3.10), min sample size from published benchmark (defect 3.7),
    MDD power statement (defect 3.21), clustered bootstrap (defect 3.20),
    WER normaliser hash pin (spec §A.2).
    """

    model_config = ConfigDict(extra="forbid")

    # TTSDS2 (D3)
    ttsds_references: list[TtsdsReferenceSet]
    ttsds_noise_reference: TtsdsNoiseReference
    ttsds_min_items: int = Field(
        description=(
            "Published minimum sample size for stable TTSDS2 (spec §A.3, "
            "verified 2026-08-06: 50-100 suffice). At 75/use-case this "
            "study clears the floor."
        ),
    )
    ttsds_split_half_threshold: float = Field(
        description=(
            "Absolute TTSDS2 delta above which split-half fails → D3 demoted "
            "to supporting signal. Absolute (not relative to noise floor) "
            "because split-half runs on first campaign slice, before noise "
            "floor exists (spec §4.3)."
        ),
    )
    ttsds_split_half_rationale: str
    ttsds_speaker_identity_handling: str = Field(
        description=(
            "Per spec §A.3 line 854: TTSDS2 warns results are best when "
            "speaker identities match ref↔test. Handling documented here "
            "before campaign since this project locks a different voice "
            "per provider by design."
        ),
    )

    # Audiobox (D3 secondary, spec B.2)
    audiobox_model_id: str
    audiobox_revision: str
    audiobox_axes_reported: list[AudioboxAxis] = Field(
        min_length=1,
        description=(
            "Pre-committed subset of the 4 axes. Reporting all 4 unlabelled "
            "would invite post-hoc selection."
        ),
    )
    audiobox_axes_rationale: str

    # WER judges (D2)
    judges: list[JudgeRevision] = Field(min_length=2, max_length=2)
    wer_normaliser: str = Field(
        description=(
            "Pinned by name+hash. Number expansion dominates jargon/edge results, "
            "so leaving normalisation to the implementer is a decisive silent "
            "difference (spec §A.2)."
        ),
    )
    wer_normaliser_hash: str = Field(
        description="Content hash of the normaliser implementation",
    )

    # Statistics
    bootstrap: BootstrapSpec = Field(default_factory=BootstrapSpec)
    mdd: MddEstimate = Field(default_factory=MddEstimate)

    @model_validator(mode="after")
    def _validate_judges_independent(self) -> AnalyzersFile:
        """Enforce spec §4.2: one Parakeet + one faster-whisper.

        Also flag if judge 1 model_id looks like TDT — the released variant is
        RNNT (defect 3.1, verified 2026-08-06). This is a soft warning encoded
        as a validation because ParakeetForTDT still requires installing
        transformers from source.
        """
        names = sorted(j.name for j in self.judges)
        if names != ["faster-whisper", "parakeet"]:
            raise ValueError(
                "analyzers.yaml judges must be exactly one `parakeet` + one "
                "`faster-whisper` (spec §4.2). Canary is not admissible as judge 2."
            )
        parakeet = next(j for j in self.judges if j.name == "parakeet")
        if "tdt" in parakeet.model_id.lower() and parakeet.revision.startswith("TODO"):
            raise ValueError(
                f"analyzers.yaml judge 1 uses TDT ({parakeet.model_id}) with an "
                "unpinned revision. ParakeetForTDT exists only on transformers `main` "
                "(spec B.3). Use `nvidia/parakeet-rnnt-*` unless TDT has landed in a "
                "release and you have pinned the exact SHA."
            )
        return self

    def reference_for(self, use_case: UseCase) -> TtsdsReferenceSet:
        for r in self.ttsds_references:
            if r.use_case == use_case:
                return r
        raise KeyError(f"No TTSDS2 reference set for use case `{use_case}`")


# --- pricing.yaml ----------------------------------------------------------


class PricingCell(BaseModel):
    """One priced billing dimension for one provider (D6)."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    tier: str = Field(description="e.g. `paid`, `free`, `Creator`, `Pro`")
    unit: Literal[
        "per_1M_chars",
        "per_1M_bytes",
        "per_generation",
        "per_1M_seconds",
        "per_1M_tokens",
    ]
    rate_usd: float = Field(description="Rate in USD per unit above")
    included_units_per_month: float | None = Field(
        default=None,
        description=(
            "Included allowance per month at this tier (in `unit`). E.g. "
            "ElevenLabs Creator = 121K credits/month at $22 (defect 3.14)."
        ),
    )
    minimum_monthly_usd: float = Field(default=0.0)
    per_request_fee_usd: float = Field(default=0.0)
    source_url: str
    date_verified: str = Field(description="ISO date the rate was checked (YYYY-MM-DD)")
    notes: str = ""


class PricingFile(BaseModel):
    """pricing.yaml — re-pulled and re-date-stamped on analysis day (D6 rule)."""

    model_config = ConfigDict(extra="forbid")

    pricing: list[PricingCell]

    def for_provider(self, provider: str) -> list[PricingCell]:
        return [c for c in self.pricing if c.provider == provider]


# --- corpus/*.yaml ---------------------------------------------------------


class CorpusItem(BaseModel):
    """One item in the corpus. `id` is stable across strata for cross-referencing."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable id, e.g. `S01`, `M12`, `L04`, `J07`, `E03`, `P02`")
    stratum: Stratum
    text: str
    word_count: int
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_word_count(self) -> CorpusItem:
        actual = len(self.text.split())
        if abs(actual - self.word_count) > 1:
            raise ValueError(
                f"CorpusItem {self.id}: declared word_count={self.word_count} "
                f"but text has {actual} words"
            )
        return self


class CorpusFile(BaseModel):
    """One use case's corpus. 75 items per use case (60 novel + 15 probe) per spec §3.3."""

    model_config = ConfigDict(extra="forbid")

    use_case: UseCase
    items: list[CorpusItem]

    @model_validator(mode="after")
    def _validate_ids_unique(self) -> CorpusFile:
        ids = [i.id for i in self.items]
        if len(ids) != len(set(ids)):
            dupes = {x for x in ids if ids.count(x) > 1}
            raise ValueError(f"CorpusFile duplicate ids: {dupes}")
        return self

    def by_stratum(self, stratum: Stratum) -> list[CorpusItem]:
        return [i for i in self.items if i.stratum == stratum]


class VarianceSubsetEntry(BaseModel):
    """corpus/variance_subset.yaml — per-use-case list of 10 items.

    Orpheus is NO LONGER reduced to 5 items — the $0.08/gen cost estimate
    was wrong by 24× (defect 3.6, actual is ~$0.003/gen). All 6 providers
    now run the full 10-item subset.
    """

    model_config = ConfigDict(extra="forbid")

    use_case: UseCase
    item_ids: list[str] = Field(
        min_length=10,
        max_length=10,
        description="Exactly 10 items per use case; all providers run the full subset",
    )
    rationale: str = Field(description="One line: how these items span the strata")


class VarianceSubset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subsets: list[VarianceSubsetEntry]

    def item_ids_for(self, use_case: UseCase) -> list[str]:
        for s in self.subsets:
            if s.use_case == use_case:
                return s.item_ids
        raise KeyError(f"No variance subset for use case `{use_case}`")


# --- Loaders ---------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


def load_providers(path: Path) -> ProvidersFile:
    return ProvidersFile.model_validate(_load_yaml(path))


def load_voices(path: Path) -> VoicesFile:
    return VoicesFile.model_validate(_load_yaml(path))


def load_gates(path: Path) -> GatesFile:
    return GatesFile.model_validate(_load_yaml(path))


def load_analyzers(path: Path) -> AnalyzersFile:
    return AnalyzersFile.model_validate(_load_yaml(path))


def load_pricing(path: Path) -> PricingFile:
    return PricingFile.model_validate(_load_yaml(path))


def load_corpus(path: Path) -> CorpusFile:
    return CorpusFile.model_validate(_load_yaml(path))


def load_variance_subset(path: Path) -> VarianceSubset:
    return VarianceSubset.model_validate(_load_yaml(path))
