"""Analyzer package — pure functions of the run store.

Every module here reads from `runs/<run_id>/` and writes to
`analysis/<run_id>/`. Run dirs are never mutated (CLAUDE.md convention),
so any analyzer can be re-run without regenerating audio.

Build order (v2 plan):
    acceptance  — WAV acceptance gate (guardrail; the Phase A silent-corruption class)
    hygiene     — clipping, LUFS, silero-VAD, acoustic noise floor
    latency     — TTFA p50/p90, RTF on long items
    cost        — pricing.yaml × char counts → cost_model.json
    wer         — Parakeet-HF + faster-whisper agreement + failure incidence + events
    quality     — TTSDS2 + Audiobox + split-half stability
    variance    — pooled within-provider SD → statistical noise floor
    drift       — per-third TTSDS2 on 8 long narration items
"""

from __future__ import annotations
