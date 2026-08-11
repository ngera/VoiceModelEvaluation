"""Config loading. config.py promises "typos fail loud" — these hold it to it.

These configs are the pre-registered ones (git-tagged `prereg-v1`), so a typo
that silently loads as a default is worse here than a crash: it would change
what was measured while still looking pre-committed.

Fixture shapes match the v2-corrected schema per DEFECT_REGISTER.md:
  - VoiceSelection carries `model` (per-use-case; defect 3.37)
  - ProviderConfig no longer carries `model`
  - GatesFile has `measurement_noise_floor` (not `noise_floor_rule`), plus
    `wer_bands`, `catastrophic_events`, and hygiene renamed to
    `acoustic_noise_floor_dbfs_max` (defect 3.19, 3.24, 3.39, 3.40)
  - AnalyzersFile has noise reference, Audiobox axes pre-commit, WER
    normaliser pin, bootstrap + MDD (defects 3.9, 3.10, 3.20, 3.21)
  - Gate carries `na_policy` and `robustness_points` (defects 3.22, 3.40)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from veval.config import (
    load_analyzers,
    load_corpus,
    load_gates,
    load_pricing,
    load_providers,
    load_variance_subset,
    load_voices,
)

VALID_PROVIDERS = """
providers:
  - name: deepgram
    display_name: "Deepgram Aura-2"
    env_key: DEEPGRAM_API_KEY
    tier: control
    notes: "Off-index control."
"""

VALID_VOICES = """
voices:
  - provider: deepgram
    use_case: conversational
    voice_id: aura-2-thalia-en
    model: aura-2-thalia-en
    reasoning: "Neutral US English."
  - provider: fish
    use_case: conversational
    voice_id: any-english-voice
    model: s2.1-pro
    split_model_from_quality: true
    quality_model: s2.1-pro-free
    reasoning: "Split: latency on paid, quality on free window."
"""

VALID_GATES = """
use_cases:
  - use_case: conversational
    gates:
      - metric: ttfa_p90_ms
        op: lt
        threshold: 400
        rationale: "400ms is deliberate headroom below the 500-600ms perception threshold."
        na_policy: exempt-and-annotate
        robustness_points: [300, 400, 500, 600]
measurement_noise_floor:
  z_multiplier: 1.96
  metrics: [ttsds2, item_wer]
  per_provider: true
  rationale: "1.96 = 95% CI on the difference of aggregates."
wer_bands:
  A_max: 0.02
  B_max: 0.05
wer_failure:
  agreement_error_rate_threshold: 0.05
  span_hard_fail: true
  span_types: [numeric, currency, date]
  rationale: "5% + span rule."
catastrophic_events:
  truncation_duration_ratio_lt: 0.60
  repetition_loop_ngram: 4
  repetition_loop_min_repeats: 3
  word_drop_min_run: 2
  hallucination_min_run: 3
hygiene:
  acoustic_noise_floor_dbfs_max: -40.0
  max_clipped_samples: 0
  rationale: "Floor for hiss; clipping is unfixable."
"""

VALID_ANALYZERS = """
ttsds_references:
  - use_case: narration
    dataset_id: daps
    rationale: "Studio-recorded read English."
  - use_case: conversational
    dataset_id: conversational
    rationale: "Spontaneous English."
ttsds_noise_reference:
  dataset_id: default
  rationale: "TTSDS2 default noise distribution."
ttsds_min_items: 50
ttsds_split_half_threshold: 0.02
ttsds_split_half_rationale: "0.02 abs delta between halves is judged stable."
ttsds_speaker_identity_handling: "Cannot match; documented as supporting-signal caveat."
audiobox_model_id: "facebook/audiobox-aesthetics"
audiobox_revision: "abc123"
audiobox_axes_reported: [production_quality, content_enjoyment]
audiobox_axes_rationale: "PQ tracks synthesis cleanliness; CE tracks preference."
dnsmos_axes_reported: [p808_mos, ovrl_mos, sig_mos, bak_mos]
dnsmos_axes_rationale: "All four axes; orthogonal concepts, no aggregation."
dnsmos_error_policy:
  input_peak_out_of_range: "peak_abs > 1 → speechmos refuses"
  other: "any other exception, classified with ExceptionType"
judges:
  - name: parakeet
    loader: transformers
    model_id: "nvidia/parakeet-rnnt-0.6b"
    revision: "sha1"
  - name: faster-whisper
    loader: ctranslate2
    model_id: "Systran/faster-whisper-large-v3"
    revision: "sha2"
wer_normaliser: "veval.analyze.wer.normalise_v1"
wer_normaliser_hash: "deadbeef"
"""

VALID_PRICING = """
pricing:
  - provider: deepgram
    tier: paid
    unit: per_1M_chars
    rate_usd: 30.0
    source_url: "https://deepgram.com/pricing"
    date_verified: "2026-08-06"
    notes: "Aura-2."
  - provider: elevenlabs
    tier: creator_monthly
    unit: per_1M_chars
    rate_usd: 50.0
    included_units_per_month: 121000
    minimum_monthly_usd: 22.0
    source_url: "https://elevenlabs.io/pricing"
    date_verified: "2026-08-06"
    notes: "Creator plan (121K credits — defect 3.14 corrected)."
"""

VALID_CORPUS = """
use_case: conversational
items:
  - id: S01
    stratum: short
    text: "The quick brown fox jumps over the lazy dog."
    word_count: 9
    tags: []
  - id: M01
    stratum: medium
    text: "This is a slightly longer sentence intended to reach the medium stratum but keep things simple."
    word_count: 16
    tags: []
"""

VALID_VARIANCE = """
subsets:
  - use_case: conversational
    item_ids: [S01, M01, M02, M03, L01, J01, J02, E01, E02, P01]
    rationale: "Spread across strata."
  - use_case: narration
    item_ids: [S01, M01, M02, L01, L02, L03, J01, E01, E02, P01]
    rationale: "Weighted toward long stratum."
"""


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


# --- providers.yaml -------------------------------------------------------


def test_load_providers_roundtrip(tmp_path: Path) -> None:
    providers = load_providers(_write(tmp_path, "providers.yaml", VALID_PROVIDERS))

    assert len(providers.providers) == 1
    entry = providers.by_name("deepgram")
    assert entry.display_name == "Deepgram Aura-2"
    assert entry.tier == "control"
    assert entry.endpoint is None


def test_providers_no_longer_carries_model_field(tmp_path: Path) -> None:
    """Defect 3.37: `model` moved to voices.yaml. A providers.yaml with `model`
    at top level should fail — silent acceptance would let a stale entry ride."""
    with_model = VALID_PROVIDERS.replace(
        "    env_key: DEEPGRAM_API_KEY\n",
        "    env_key: DEEPGRAM_API_KEY\n    model: aura-2-thalia-en\n",
    )
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", with_model))


def test_unknown_provider_key_is_rejected(tmp_path: Path) -> None:
    typo = VALID_PROVIDERS.replace("env_key:", "env_keys:")
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", typo))


def test_missing_required_field_is_rejected(tmp_path: Path) -> None:
    incomplete = VALID_PROVIDERS.replace('    display_name: "Deepgram Aura-2"\n', "")
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", incomplete))


def test_invalid_tier_is_rejected(tmp_path: Path) -> None:
    bad = VALID_PROVIDERS.replace("tier: control", "tier: premium")
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", bad))


def test_missing_file_raises_filenotfound(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_providers(tmp_path / "absent.yaml")


# --- voices.yaml ----------------------------------------------------------


def test_load_voices_and_lookup(tmp_path: Path) -> None:
    voices = load_voices(_write(tmp_path, "voices.yaml", VALID_VOICES))

    dg = voices.get("deepgram", "conversational")
    assert dg.voice_id == "aura-2-thalia-en"
    assert dg.model == "aura-2-thalia-en"
    assert dg.split_model_from_quality is False

    with pytest.raises(KeyError):
        voices.get("deepgram", "narration")


def test_voice_split_model_requires_quality_model(tmp_path: Path) -> None:
    """Defect 3.38: providers with split (quality vs latency) models must
    declare both, so the on-chart annotation can be generated."""
    bad = VALID_VOICES.replace(
        "    quality_model: s2.1-pro-free\n",
        "",
    )
    with pytest.raises(ValidationError):
        load_voices(_write(tmp_path, "voices.yaml", bad))


def test_voice_quality_model_without_split_flag_is_rejected(tmp_path: Path) -> None:
    """Flip side: quality_model set but split flag off is inconsistent."""
    bad = VALID_VOICES.replace(
        "    split_model_from_quality: true\n",
        "    split_model_from_quality: false\n",
    )
    with pytest.raises(ValidationError):
        load_voices(_write(tmp_path, "voices.yaml", bad))


def test_voice_split_case_lookup(tmp_path: Path) -> None:
    voices = load_voices(_write(tmp_path, "voices.yaml", VALID_VOICES))
    fish = voices.get("fish", "conversational")
    assert fish.split_model_from_quality is True
    assert fish.model == "s2.1-pro"  # latency
    assert fish.quality_model == "s2.1-pro-free"


def test_invalid_use_case_is_rejected(tmp_path: Path) -> None:
    bad = VALID_VOICES.replace("use_case: conversational", "use_case: podcast", 1)
    with pytest.raises(ValidationError):
        load_voices(_write(tmp_path, "voices.yaml", bad))


# --- gates.yaml -----------------------------------------------------------


def test_load_gates_roundtrip(tmp_path: Path) -> None:
    gates = load_gates(_write(tmp_path, "gates.yaml", VALID_GATES))

    conversational = gates.use_cases[0]
    assert conversational.use_case == "conversational"
    g0 = conversational.gates[0]
    assert g0.op == "lt"
    assert g0.threshold == 400
    assert g0.na_policy == "exempt-and-annotate"
    assert g0.robustness_points == [300, 400, 500, 600]

    assert gates.measurement_noise_floor.z_multiplier == 1.96
    assert gates.measurement_noise_floor.metrics == ["ttsds2", "item_wer"]
    assert gates.measurement_noise_floor.per_provider is True
    assert gates.wer_bands.A_max == 0.02
    assert gates.wer_failure.agreement_error_rate_threshold == 0.05
    assert gates.wer_failure.span_hard_fail is True
    assert "date" in gates.wer_failure.span_types
    assert gates.catastrophic_events.truncation_duration_ratio_lt == 0.60
    assert gates.hygiene.acoustic_noise_floor_dbfs_max == -40.0


def test_invalid_gate_operator_is_rejected(tmp_path: Path) -> None:
    bad = VALID_GATES.replace("op: lt", "op: less_than")
    with pytest.raises(ValidationError):
        load_gates(_write(tmp_path, "gates.yaml", bad))


def test_invalid_na_policy_is_rejected(tmp_path: Path) -> None:
    bad = VALID_GATES.replace("na_policy: exempt-and-annotate", "na_policy: ignore-quietly")
    with pytest.raises(ValidationError):
        load_gates(_write(tmp_path, "gates.yaml", bad))


def test_gates_without_measurement_noise_floor_is_rejected(tmp_path: Path) -> None:
    """v2 gate file must carry the measurement noise-floor rule."""
    incomplete = VALID_GATES.split("measurement_noise_floor:")[0] + VALID_GATES.split(
        "wer_bands:"
    )[1].split("wer_bands:")[-1]
    # Actually simpler: strip the measurement_noise_floor block by regex
    import re

    stripped = re.sub(
        r"measurement_noise_floor:\n(?:  .*\n)+", "", VALID_GATES
    )
    with pytest.raises(ValidationError):
        load_gates(_write(tmp_path, "gates.yaml", stripped))


def test_hygiene_field_is_renamed_from_v1(tmp_path: Path) -> None:
    """Defect 3.39: `noise_floor_dbfs_max` was renamed to
    `acoustic_noise_floor_dbfs_max` to disambiguate from the statistical
    measurement_noise_floor. The old name should now fail."""
    old = VALID_GATES.replace(
        "acoustic_noise_floor_dbfs_max", "noise_floor_dbfs_max"
    )
    with pytest.raises(ValidationError):
        load_gates(_write(tmp_path, "gates.yaml", old))


# --- analyzers.yaml -------------------------------------------------------


def test_load_analyzers_roundtrip(tmp_path: Path) -> None:
    analyzers = load_analyzers(_write(tmp_path, "analyzers.yaml", VALID_ANALYZERS))

    assert analyzers.ttsds_min_items == 50
    assert analyzers.ttsds_split_half_threshold == 0.02
    assert analyzers.ttsds_noise_reference.dataset_id == "default"
    assert analyzers.reference_for("narration").dataset_id == "daps"
    assert analyzers.reference_for("conversational").dataset_id == "conversational"
    assert set(analyzers.audiobox_axes_reported) == {"production_quality", "content_enjoyment"}
    assert analyzers.wer_normaliser_hash == "deadbeef"
    assert analyzers.bootstrap.cluster_by == "item"
    assert analyzers.bootstrap.resamples == 2000
    assert analyzers.mdd.n_judgments_target == 210
    assert len(analyzers.judges) == 2


def test_analyzers_rejects_canary_as_judge2(tmp_path: Path) -> None:
    """Spec §4.2: Canary shares Parakeet's encoder family + data pipeline.
    Two Parakeet judges violate the independence rule."""
    bad = VALID_ANALYZERS.replace(
        "  - name: faster-whisper", "  - name: parakeet"
    ).replace(
        '    model_id: "Systran/faster-whisper-large-v3"',
        '    model_id: "nvidia/canary-1b"',
    )
    with pytest.raises(ValidationError):
        load_analyzers(_write(tmp_path, "analyzers.yaml", bad))


def test_analyzers_flags_unpinned_tdt(tmp_path: Path) -> None:
    """Defect 3.1: ParakeetForTDT exists only on transformers `main`; the
    validator warns if TDT model_id is used with an unpinned (TODO) revision."""
    bad = VALID_ANALYZERS.replace(
        '    model_id: "nvidia/parakeet-rnnt-0.6b"',
        '    model_id: "nvidia/parakeet-tdt-0.6b"',
    ).replace('    revision: "sha1"', '    revision: "TODO_pin_sha"')
    with pytest.raises(ValidationError):
        load_analyzers(_write(tmp_path, "analyzers.yaml", bad))


def test_analyzers_allows_tdt_when_pinned(tmp_path: Path) -> None:
    """Phase B might land TDT in a release — allowed if a real SHA is pinned."""
    ok = VALID_ANALYZERS.replace(
        '    model_id: "nvidia/parakeet-rnnt-0.6b"',
        '    model_id: "nvidia/parakeet-tdt-0.6b-v2"',
    )
    # revision remains "sha1" — a real SHA — should pass
    load_analyzers(_write(tmp_path, "analyzers.yaml", ok))


def test_analyzers_requires_at_least_one_audiobox_axis(tmp_path: Path) -> None:
    bad = VALID_ANALYZERS.replace(
        "audiobox_axes_reported: [production_quality, content_enjoyment]",
        "audiobox_axes_reported: []",
    )
    with pytest.raises(ValidationError):
        load_analyzers(_write(tmp_path, "analyzers.yaml", bad))


def test_analyzers_rejects_unknown_axis(tmp_path: Path) -> None:
    bad = VALID_ANALYZERS.replace(
        "audiobox_axes_reported: [production_quality, content_enjoyment]",
        "audiobox_axes_reported: [production_quality, magic_naturalness]",
    )
    with pytest.raises(ValidationError):
        load_analyzers(_write(tmp_path, "analyzers.yaml", bad))


def test_analyzers_rejects_unknown_judge_loader(tmp_path: Path) -> None:
    bad = VALID_ANALYZERS.replace("loader: transformers", "loader: torch_hub")
    with pytest.raises(ValidationError):
        load_analyzers(_write(tmp_path, "analyzers.yaml", bad))


# --- pricing.yaml ---------------------------------------------------------


def test_load_pricing_roundtrip(tmp_path: Path) -> None:
    pricing = load_pricing(_write(tmp_path, "pricing.yaml", VALID_PRICING))

    dg = pricing.for_provider("deepgram")
    assert len(dg) == 1
    assert dg[0].unit == "per_1M_chars"
    assert dg[0].rate_usd == 30.0

    el = pricing.for_provider("elevenlabs")[0]
    assert el.included_units_per_month == 121000  # defect 3.14
    assert el.minimum_monthly_usd == 22.0


def test_pricing_rejects_unknown_unit(tmp_path: Path) -> None:
    bad = VALID_PRICING.replace("unit: per_1M_chars", "unit: per_minute", 1)
    with pytest.raises(ValidationError):
        load_pricing(_write(tmp_path, "pricing.yaml", bad))


# --- corpus/*.yaml --------------------------------------------------------


def test_load_corpus_roundtrip(tmp_path: Path) -> None:
    corpus = load_corpus(_write(tmp_path, "conversational.yaml", VALID_CORPUS))

    assert corpus.use_case == "conversational"
    assert len(corpus.items) == 2
    assert len(corpus.by_stratum("short")) == 1


def test_corpus_rejects_duplicate_ids(tmp_path: Path) -> None:
    dup = VALID_CORPUS.replace("id: M01", "id: S01")
    with pytest.raises(ValidationError):
        load_corpus(_write(tmp_path, "conversational.yaml", dup))


def test_corpus_rejects_wrong_word_count(tmp_path: Path) -> None:
    bad = VALID_CORPUS.replace("word_count: 9", "word_count: 20")
    with pytest.raises(ValidationError):
        load_corpus(_write(tmp_path, "conversational.yaml", bad))


# --- variance_subset.yaml -------------------------------------------------


def test_load_variance_subset_roundtrip(tmp_path: Path) -> None:
    subset = load_variance_subset(_write(tmp_path, "variance_subset.yaml", VALID_VARIANCE))
    assert subset.item_ids_for("conversational")[0] == "S01"
    assert len(subset.item_ids_for("narration")) == 10


def test_variance_subset_requires_exactly_10_items(tmp_path: Path) -> None:
    """Defect 3.6: Orpheus 5-item reduction was based on wrong cost estimate.
    All 6 providers now run the full 10-item subset; the schema enforces it."""
    bad = VALID_VARIANCE.replace(
        "item_ids: [S01, M01, M02, M03, L01, J01, J02, E01, E02, P01]",
        "item_ids: [S01, M01, M02, M03, L01]",
    )
    with pytest.raises(ValidationError):
        load_variance_subset(_write(tmp_path, "variance_subset.yaml", bad))


# --- Shipped configs must actually load -----------------------------------


def test_shipped_providers_yaml_is_valid() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    providers = load_providers(repo_root / "configs" / "providers.yaml")
    names = {p.name for p in providers.providers}
    # Original 6 (prereg-v1) + OpenAI, Speechify (prereg-v1.1, DEVIATIONS D-003)
    assert names == {
        "deepgram", "fish", "google", "cartesia", "elevenlabs", "orpheus",
        "openai", "speechify",
    }


def test_shipped_gates_yaml_is_valid() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    gates = load_gates(repo_root / "configs" / "gates.yaml")
    # Corrected fields per defects 3.19, 3.24, 3.39
    assert gates.measurement_noise_floor.z_multiplier == 1.96
    assert gates.wer_failure.agreement_error_rate_threshold == 0.05
    assert gates.wer_failure.span_hard_fail is True
    assert gates.hygiene.acoustic_noise_floor_dbfs_max == -40.0
    # Every gate must have robustness_points defined
    for uc in gates.use_cases:
        for g in uc.gates:
            assert g.robustness_points, f"Gate {g.metric} has no robustness_points"


def test_shipped_analyzers_yaml_is_valid() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    analyzers = load_analyzers(repo_root / "configs" / "analyzers.yaml")
    names = sorted(j.name for j in analyzers.judges)
    # D-010 (prereg-v1.9): judge 1 swapped from `parakeet` (didn't load via
    # released `transformers`) to `wav2vec2`. Test tolerates either.
    admissible_judge_1 = {"parakeet", "wav2vec2"}
    assert "faster-whisper" in names
    other = [n for n in names if n != "faster-whisper"][0]
    assert other in admissible_judge_1, (
        f"Judge 1 must be one of {admissible_judge_1}; got {other!r}"
    )
    # Defect 3.7: min items must clear the published floor (50-100)
    assert analyzers.ttsds_min_items >= 50
    # Defect 3.10: axes must be pre-committed
    assert 1 <= len(analyzers.audiobox_axes_reported) <= 4


def test_shipped_pricing_yaml_is_valid() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    pricing = load_pricing(repo_root / "configs" / "pricing.yaml")
    providers = load_providers(repo_root / "configs" / "providers.yaml")
    for p in providers.providers:
        assert pricing.for_provider(p.name), f"No pricing for {p.name}"

    # Defect 3.6: Orpheus must be ~$0.003/gen, not $0.08
    orpheus_rows = pricing.for_provider("orpheus")
    assert orpheus_rows[0].rate_usd < 0.01, (
        f"Orpheus rate {orpheus_rows[0].rate_usd} looks like the pre-fix $0.08 value"
    )

    # Defect 3.14: ElevenLabs Creator must include 121K credits, not 100K
    el_creator = [c for c in pricing.for_provider("elevenlabs") if "creator" in c.tier.lower()]
    assert any(c.included_units_per_month == 121000 for c in el_creator), (
        "ElevenLabs Creator should include 121K credits per defect 3.14"
    )


def test_shipped_voices_yaml_is_valid() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    voices = load_voices(repo_root / "configs" / "voices.yaml")
    providers = load_providers(repo_root / "configs" / "providers.yaml")
    for p in providers.providers:
        for uc in ("conversational", "narration"):
            selection = voices.get(p.name, uc)  # type: ignore[arg-type]
            assert selection.voice_id, f"Empty voice_id for {p.name} × {uc}"
            assert selection.model, f"Empty model for {p.name} × {uc}"


def test_shipped_voices_split_flag_matches_providers_notes() -> None:
    """The `split_model_from_quality` flag should light up for Fish (both
    use cases) since Fish is the only split-model provider in the roster."""
    repo_root = Path(__file__).resolve().parent.parent
    voices = load_voices(repo_root / "configs" / "voices.yaml")

    split = [(v.provider, v.use_case) for v in voices.voices if v.split_model_from_quality]
    assert ("fish", "conversational") in split
    assert ("fish", "narration") in split
    # No other provider is currently split
    non_fish_split = [(p, uc) for (p, uc) in split if p != "fish"]
    assert not non_fish_split, f"Unexpected split-model providers: {non_fish_split}"
