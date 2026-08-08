"""WER analyzer — two-judge agreement + failure incidence + catastrophic events.

Judges (spec §4.2, analyzers.yaml):
    - Parakeet RNNT 0.6B via HuggingFace `transformers`
    - faster-whisper large-v3 via `ctranslate2`
Judges must differ in org, architecture family, and training pipeline
(§4.2). Canary is *not* admissible as judge 2 — same NVIDIA family as
Parakeet.

Two-judge agreement:
    - Each judge transcribes the WAV. Both transcripts are normalised
      by `normalise_v1` (single canonical implementation, hash-pinned
      in analyzers.yaml).
    - Item-level WER uses `jiwer.wer(reference, hypothesis)` where the
      hypothesis is the AGREED tokens between judges and the reference
      is the corpus text (also normalised). Words the judges disagreed
      on are conservatively kept as errors — a real error should be
      seen by both.

Per-item failure (gates.yaml `wer_failure`):
    - agreement_error_rate > 0.05, OR
    - any agreed deletion/substitution inside a numeric, currency, or
      date span in the source text ("one mangled dollar amount matters
      more than five wrong function words").

Catastrophic events (gates.yaml `catastrophic_events`):
    - truncation: decoded < 60% of predicted-from-char-count duration
    - repetition_loop: 4-gram repeated ≥3 times in BOTH transcripts
    - word_drop: agreed deletion run of ≥2 tokens
    - hallucination: agreed insertion run of ≥3 tokens

Bands (gates.yaml `wer_bands`):
    A ≤ 2% · B ≤ 5% · C > 5%
"""

from __future__ import annotations

import hashlib
import inspect
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from veval.config import AnalyzersFile, CorpusFile, GatesFile

from .common import AnalysisWriter, AudioRecord, RunReader

CHARS_PER_WORD = 5.0
# 150 wpm = 2.5 wps; each word ≈ 5 chars → ~12.5 chars/sec. Used as the
# ratio for the truncation detector. Loose bound — the gate threshold is
# 0.60, so real speech-rate variation is well inside tolerance.
CHARS_PER_SECOND = 12.5


# --- normaliser_v1 --------------------------------------------------------


def normalise_v1(text: str) -> str:
    """Canonical text normaliser for WER computation.

    Pinned by name + content-hash in analyzers.yaml. Number expansion
    dominates jargon/edge results (spec §A.2), so leaving normalisation
    to the implementer is a decisive silent difference. Reference and
    hypothesis both pass through this before jiwer sees them.

    Steps:
        1. lowercase
        2. strip common contractions to canonical form ("don't" → "do not")
        3. drop punctuation (keep hyphens inside compounds via letter boundary)
        4. collapse runs of whitespace

    Number expansion is intentionally NOT done here — the whisper/
    parakeet judges emit digits or words depending on their own
    normalisation; forcing one representation would advantage
    whichever happens to match. Spans are handled by the failure rule
    (below), not by normalisation.
    """
    text = text.lower()
    contractions = {
        "won't": "will not",
        "can't": "cannot",
        "n't": " not",
        "'re": " are",
        "'ve": " have",
        "'ll": " will",
        "'d": " would",
        "'m": " am",
        "'s": " is",
    }
    for k, v in contractions.items():
        text = text.replace(k, v)
    # Drop punctuation but preserve intra-word hyphens/apostrophes (already
    # handled above). Keep alphanumerics + whitespace + hyphen between letters.
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


NORMALISER_HASH = hashlib.sha256(
    inspect.getsource(normalise_v1).encode("utf-8")
).hexdigest()


# --- Span detection (numeric / currency / date) ---------------------------


NUMBER_RE = re.compile(r"\b\d[\d,\.]*\b")
CURRENCY_RE = re.compile(
    r"\$\s?\d[\d,\.]*|\b\d[\d,\.]*\s?(?:dollars?|cents?|usd|eur|gbp)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:,\s*\d{2,4})?"
    r"|\b\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b"
    r"|\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b",
    re.IGNORECASE,
)


def extract_spans(text: str) -> list[tuple[str, str]]:
    """Return list of (span_type, span_text) tuples found in text.

    Order-independent; the failure rule only checks whether an agreed
    error falls INSIDE any span, not which one.
    """
    spans: list[tuple[str, str]] = []
    for m in NUMBER_RE.finditer(text):
        spans.append(("numeric", m.group(0)))
    for m in CURRENCY_RE.finditer(text):
        spans.append(("currency", m.group(0)))
    for m in DATE_RE.finditer(text):
        spans.append(("date", m.group(0)))
    return spans


# --- Two-judge agreement --------------------------------------------------


def agreed_tokens(judge_a: str, judge_b: str) -> tuple[list[str], list[str]]:
    """Return (agreed, disputed) tokens.

    "Agreed" = tokens present at the same aligned position in both
    normalised transcripts. Uses jiwer's word-level alignment.
    """
    from jiwer import process_words

    out = process_words(judge_a, judge_b)
    # process_words returns alignment per-sentence; grab the first
    # (each judge produces one utterance).
    alignments = out.alignments[0] if out.alignments else []
    a_words = out.references[0] if out.references else []

    agreed: list[str] = []
    disputed: list[str] = []
    for align in alignments:
        if align.type == "equal":
            agreed.extend(a_words[align.ref_start_idx:align.ref_end_idx])
        else:
            # For failure-span analysis we need to know WHICH tokens
            # were disputed on the *reference* (parakeet) side.
            disputed.extend(a_words[align.ref_start_idx:align.ref_end_idx])
    return agreed, disputed


# --- Catastrophic-event detectors ----------------------------------------


def detect_repetition_loop(
    tokens: list[str],
    ngram: int = 4,
    min_repeats: int = 3,
) -> bool:
    """True when any n-gram repeats ≥ min_repeats times consecutively."""
    if len(tokens) < ngram * min_repeats:
        return False
    for i in range(len(tokens) - ngram * min_repeats + 1):
        first = tokens[i:i + ngram]
        ok = True
        for k in range(1, min_repeats):
            window = tokens[i + k * ngram: i + (k + 1) * ngram]
            if window != first:
                ok = False
                break
        if ok:
            return True
    return False


def detect_agreed_deletion_run(
    reference_words: list[str],
    hypothesis_words: list[str],
    min_run: int = 2,
) -> int:
    """Count runs of ≥min_run consecutive deleted tokens (per jiwer alignment)."""
    from jiwer import process_words

    out = process_words(" ".join(reference_words), " ".join(hypothesis_words))
    alignments = out.alignments[0] if out.alignments else []
    runs = 0
    for align in alignments:
        if align.type == "delete":
            span = align.ref_end_idx - align.ref_start_idx
            if span >= min_run:
                runs += 1
    return runs


def detect_agreed_insertion_run(
    reference_words: list[str],
    hypothesis_words: list[str],
    min_run: int = 3,
) -> int:
    """Count runs of ≥min_run consecutive inserted tokens."""
    from jiwer import process_words

    out = process_words(" ".join(reference_words), " ".join(hypothesis_words))
    alignments = out.alignments[0] if out.alignments else []
    runs = 0
    for align in alignments:
        if align.type == "insert":
            span = align.hyp_end_idx - align.hyp_start_idx
            if span >= min_run:
                runs += 1
    return runs


def detect_truncation(
    decoded_seconds: float | None,
    reference_chars: int,
    ratio_threshold: float = 0.60,
) -> bool:
    """True when decoded audio < ratio × predicted-from-chars duration."""
    if decoded_seconds is None or reference_chars <= 0:
        return False
    predicted = reference_chars / CHARS_PER_SECOND
    if predicted <= 0:
        return False
    return (decoded_seconds / predicted) < ratio_threshold


# --- Judge loaders (lazy) ------------------------------------------------


_PARAKEET: Any = None
_WHISPER: Any = None


def _load_parakeet(model_id: str, revision: str) -> Any:
    global _PARAKEET
    if _PARAKEET is None:
        from transformers import pipeline

        _PARAKEET = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            revision=revision if not revision.startswith("TODO") else None,
        )
    return _PARAKEET


def _load_whisper(model_id: str, revision: str) -> Any:
    global _WHISPER
    if _WHISPER is None:
        from faster_whisper import WhisperModel

        # faster-whisper takes the model id directly; revision pin lives
        # in analyzers.yaml but ctranslate2 doesn't accept it as a param —
        # we pin the huggingface_hub cache by hash separately.
        _WHISPER = WhisperModel(model_id, device="cpu", compute_type="int8")
    return _WHISPER


def _transcribe_parakeet(pipeline_obj: Any, wav_path: Path) -> str:
    out = pipeline_obj(str(wav_path))
    return str(out.get("text", "")).strip() if isinstance(out, dict) else str(out).strip()


def _transcribe_whisper(model: Any, wav_path: Path) -> str:
    segments, _info = model.transcribe(str(wav_path), language="en", beam_size=1)
    return " ".join(seg.text.strip() for seg in segments).strip()


# --- Per-file analysis ----------------------------------------------------


@dataclass
class WerItem:
    provider: str
    use_case: str
    item_id: str
    draw: int
    stratum: str | None
    reference: str
    parakeet: str
    whisper: str
    agreement_wer: float | None
    per_judge_wer: dict[str, float] = field(default_factory=dict)
    failure: bool = False
    failure_reasons: list[str] = field(default_factory=list)
    events: dict[str, Any] = field(default_factory=dict)
    band: str | None = None
    error: str | None = None


def _band(wer: float, wer_bands: Any) -> str:
    if wer <= wer_bands.A_max:
        return "A"
    if wer <= wer_bands.B_max:
        return "B"
    return "C"


def _stratum(item_id: str) -> str | None:
    if not item_id:
        return None
    return {"S": "short", "M": "medium", "L": "long", "J": "jargon", "E": "edge", "P": "probe"}.get(
        item_id[0].upper()
    )


def analyze_file(
    record: AudioRecord,
    *,
    reference_text: str,
    parakeet_pipe: Any,
    whisper_model: Any,
    gates: GatesFile,
    decoded_seconds: float | None = None,
) -> WerItem:
    from jiwer import wer as jiwer_wer

    r = WerItem(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
        stratum=_stratum(record.item_id),
        reference=reference_text,
        parakeet="",
        whisper="",
        agreement_wer=None,
    )
    if not record.wav_path.exists():
        r.error = "wav_missing"
        return r

    try:
        r.parakeet = _transcribe_parakeet(parakeet_pipe, record.wav_path)
        r.whisper = _transcribe_whisper(whisper_model, record.wav_path)
    except Exception as e:  # noqa: BLE001 — model errors are data
        r.error = f"asr_error={e.__class__.__name__}: {e}"
        return r

    ref_n = normalise_v1(reference_text)
    par_n = normalise_v1(r.parakeet)
    whi_n = normalise_v1(r.whisper)

    r.per_judge_wer = {
        "parakeet": float(jiwer_wer(ref_n, par_n)) if ref_n else None,
        "whisper": float(jiwer_wer(ref_n, whi_n)) if ref_n else None,
    }

    # Agreement WER: score reference vs the agreed tokens between judges.
    # Disputed tokens between judges become "errors" against the reference
    # — the conservative direction.
    agreed, _disputed = agreed_tokens(par_n, whi_n)
    agreed_hyp = " ".join(agreed)
    r.agreement_wer = float(jiwer_wer(ref_n, agreed_hyp)) if ref_n else None
    r.band = (
        _band(r.agreement_wer, gates.wer_bands) if r.agreement_wer is not None else None
    )

    # Failure rule
    fail_thresh = gates.wer_failure.agreement_error_rate_threshold
    if r.agreement_wer is not None and r.agreement_wer > fail_thresh:
        r.failure = True
        r.failure_reasons.append(
            f"agreement_wer={r.agreement_wer:.3f} > {fail_thresh}"
        )
    # Span hard-fail: any agreed miss inside a numeric/currency/date span
    if gates.wer_failure.span_hard_fail:
        spans = extract_spans(reference_text)
        if spans and _spans_missed(agreed_hyp, spans):
            r.failure = True
            r.failure_reasons.append("span_agreed_miss")

    # Catastrophic events (thresholds from gates)
    ce = gates.catastrophic_events
    r.events = {
        "truncation": detect_truncation(
            decoded_seconds, len(reference_text), ce.truncation_duration_ratio_lt
        ),
        "repetition_loop_parakeet": detect_repetition_loop(
            par_n.split(), ce.repetition_loop_ngram, ce.repetition_loop_min_repeats
        ),
        "repetition_loop_whisper": detect_repetition_loop(
            whi_n.split(), ce.repetition_loop_ngram, ce.repetition_loop_min_repeats
        ),
        "agreed_word_drop_runs": detect_agreed_deletion_run(
            ref_n.split(), agreed_hyp.split(), ce.word_drop_min_run
        ),
        "agreed_hallucination_runs": detect_agreed_insertion_run(
            ref_n.split(), agreed_hyp.split(), ce.hallucination_min_run
        ),
    }
    return r


def _spans_missed(agreed_hyp: str, spans: list[tuple[str, str]]) -> bool:
    """Any span whose normalised form is NOT present in the agreed hypothesis
    counts as a span-agreed miss.
    """
    hyp_n = agreed_hyp
    for _, span in spans:
        if normalise_v1(span) not in hyp_n:
            return True
    return False


# --- Aggregation + run() --------------------------------------------------


def _aggregate(rows: list[WerItem]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[WerItem]] = {}
    for r in rows:
        groups.setdefault((r.provider, r.use_case), []).append(r)

    out: list[dict[str, Any]] = []
    for (provider, use_case), items in sorted(groups.items()):
        valid = [i for i in items if i.error is None and i.agreement_wer is not None]
        n = len(valid)
        n_failure = sum(1 for i in valid if i.failure)
        out.append({
            "provider": provider,
            "use_case": use_case,
            "n_items": len(items),
            "n_valid": n,
            "n_errors": len(items) - n,
            "agreement_wer_mean": (sum(i.agreement_wer for i in valid) / n) if n else None,
            "failure_incidence_pct": (100.0 * n_failure / n) if n else None,
            "band_counts": {b: sum(1 for i in valid if i.band == b) for b in ("A", "B", "C")},
            "event_counts": {
                "truncation": sum(1 for i in valid if i.events.get("truncation")),
                "repetition_loop": sum(
                    1
                    for i in valid
                    if i.events.get("repetition_loop_parakeet")
                    or i.events.get("repetition_loop_whisper")
                ),
                "word_drop": sum(
                    int(i.events.get("agreed_word_drop_runs", 0) > 0) for i in valid
                ),
                "hallucination": sum(
                    int(i.events.get("agreed_hallucination_runs", 0) > 0) for i in valid
                ),
            },
        })
    return out


def _resolve_reference(corpus_by_use_case: dict[str, CorpusFile], record: AudioRecord) -> str:
    corpus = corpus_by_use_case.get(record.use_case)
    if corpus is None:
        return ""
    for item in corpus.items:
        if item.id == record.item_id:
            return item.text
    return ""


def run(
    run_dir: Path,
    *,
    gates: GatesFile,
    analyzers: AnalyzersFile,
    corpus_by_use_case: dict[str, CorpusFile],
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Run WER analysis. Downloads Parakeet + faster-whisper on first call
    (cached thereafter). Writes `wer.json`.
    """
    parakeet_cfg = next(j for j in analyzers.judges if j.name == "parakeet")
    whisper_cfg = next(j for j in analyzers.judges if j.name == "faster-whisper")
    parakeet_pipe = _load_parakeet(parakeet_cfg.model_id, parakeet_cfg.revision)
    whisper_model = _load_whisper(whisper_cfg.model_id, whisper_cfg.revision)

    reader = RunReader(run_dir)
    rows: list[WerItem] = []
    for record in reader.records():
        reference = _resolve_reference(corpus_by_use_case, record)
        if not reference:
            rows.append(WerItem(
                provider=record.provider, use_case=record.use_case,
                item_id=record.item_id, draw=record.draw, stratum=_stratum(record.item_id),
                reference="", parakeet="", whisper="", agreement_wer=None,
                error="reference_not_in_corpus",
            ))
            continue
        # Decoded duration (for truncation detector) — cheap to compute here
        try:
            import soundfile as sf
            info = sf.info(str(record.wav_path))
            decoded_seconds = float(info.duration)
        except Exception:  # noqa: BLE001
            decoded_seconds = None
        rows.append(analyze_file(
            record,
            reference_text=reference,
            parakeet_pipe=parakeet_pipe,
            whisper_model=whisper_model,
            gates=gates,
            decoded_seconds=decoded_seconds,
        ))

    payload = {
        "run_id": run_dir.name,
        "normaliser": "veval.analyze.wer.normalise_v1",
        "normaliser_hash": NORMALISER_HASH,
        "judges": {
            j.name: {"model_id": j.model_id, "revision": j.revision}
            for j in analyzers.judges
        },
        "bands": {"A_max": gates.wer_bands.A_max, "B_max": gates.wer_bands.B_max},
        "failure_rule": {
            "agreement_error_rate_threshold": gates.wer_failure.agreement_error_rate_threshold,
            "span_hard_fail": gates.wer_failure.span_hard_fail,
        },
        "by_provider": _aggregate(rows),
        "items": [asdict(r) for r in rows],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("wer.json", payload)
    return payload
