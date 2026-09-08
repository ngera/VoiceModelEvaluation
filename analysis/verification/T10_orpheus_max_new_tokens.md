# T10 — Orpheus `max_new_tokens` cap check

**Date**: 2026-09-07
**Verdict**: **Confirmed as deployment-config default (bounded)** — the 14.59-s
cap is NOT model-intrinsic; passing `max_new_tokens = 2000` produces
**24.32 s** of audio (67% longer). But Replicate's own wrapper hard-caps
`max_new_tokens` at 2000, so the fix is bounded: **the practical Orpheus
ceiling on Replicate is ~24 s per call, not unbounded**.

---

## Hypothesis

The Orpheus 14.59-s per-call output cap (F-5, T8) is a deployment-config
default (Replicate wrapper's `max_new_tokens` parameter) rather than a
model-intrinsic architectural limit. Passing `max_new_tokens = 4000` on a
long-narration item should produce output substantially longer than 14.59 s.

## Method

One Replicate call to `lucataco/orpheus-3b-0.1-ft`
(version `79f2a473e6a9720716a473d9b2f2951437dbf91dc02ccb7079fb3d89b881207f`,
per D-005 pin at `configs/providers.yaml`) with:

- `text`: L01 narration item (`corpus/narration.yaml`), 1,313 chars / 233 words
- `voice`: `dan` — **this is the pinned narration voice**, per
  `configs/voices.yaml` (the `leo` pick was replaced pre-verification when
  the Replicate fork's enum turned out to be `{tara, dan, josh, emma}`; the
  comment at that entry records the swap). So this test ran on the pinned
  voice, not a substitute.
- `max_new_tokens`: initially 4000, then 2000

Script: [`scripts/_t10_orpheus_max_new_tokens.py`](../../scripts/_t10_orpheus_max_new_tokens.py).

## Result

Two-step because the Replicate wrapper itself has a schema-level cap:

1. **First call, `max_new_tokens = 4000`** → HTTP 422:
   `"input.max_new_tokens: Must be less than or equal to 2000"`. That
   422 IS a partial answer on its own — the cap is enforced at the
   Replicate wrapper's JSON schema, above the model, which is
   deployment-config territory by definition.

2. **Second call, `max_new_tokens = 2000` (wrapper ceiling)** → succeeded:
   - Output duration: **24.32 s**
   - Sample rate: 24 kHz
   - Audio bytes: 1,167,404
   - Wall clock: 137.3 s

Baseline from T8: default output cap is 14.59 s ± 0.000 s across 8 long-narration
items. `max_new_tokens = 2000` produces **24.32 s / 14.59 s = 1.667× more audio
per call**.

## Interpretation

**The 14.59-s cap is the Replicate wrapper's default `max_new_tokens` value
(not passed = uses the schema default), not a model-intrinsic architectural
limit.** Raising `max_new_tokens` to 2000 (the wrapper's own ceiling) unlocks
1.67× more output.

**But the fix is bounded, not unbounded**: Replicate's wrapper JSON schema
hard-caps `max_new_tokens` at 2000, so the practical Orpheus-on-Replicate
ceiling is ~24 s per call. Full-length narration items in our corpus
(L01–L08 average ~200 words ≈ ~85 s of clean speech) would still need
chunking; the fix reduces the number of chunks by ~1.67× rather than
eliminating chunking entirely.

## PM recommendation — collapse from "either / or" to bounded fix

Prior wording ("Cap may be model-intrinsic OR a deployment-config parameter
— untested; recommendations differ") is resolved. Recommended framing going
forward:

> Orpheus on Replicate's hosted `lucataco/orpheus-3b-0.1-ft` caps at 14.59 s
> per call by default and at ~24 s per call with `max_new_tokens = 2000`
> (Replicate's wrapper ceiling). Long-form narration still needs chunking;
> the max_new_tokens flag reduces chunk count by ~1.67× rather than
> eliminating it. If you self-host the base Orpheus model (bypassing the
> Replicate wrapper) the ceiling is presumably higher — untested here.

## Cost implication

Original T8 per-1K-words cost under the 14.59-s cap:
**~$0.067–$0.088 per 1K words** (F-5, CORRECTIONS row 5). At
`max_new_tokens = 2000` (24.32-s cap), the same fixed per-call Replicate
cost delivers 1.67× more audio per call, so per-1K-words drops to roughly:

- **~$0.040–$0.053 per 1K words** at the raised cap

Still peer-priced to OpenAI ($0.075) rather than at the nominal $0.030 in
pricing.yaml (which assumes ~100 words per call and predates T8's per-call
measurement). Orpheus-on-Replicate remains a chunked-workflow proposition,
not a drop-in narration vendor.

## Artefacts

- Verdict JSON: [`T10_orpheus_max_new_tokens/T10_verdict.json`](T10_orpheus_max_new_tokens/T10_verdict.json)
- Audio: [`T10_orpheus_max_new_tokens/T10_L01_max_new_tokens_2000.wav`](T10_orpheus_max_new_tokens/T10_L01_max_new_tokens_2000.wav)
- Script: [`scripts/_t10_orpheus_max_new_tokens.py`](../../scripts/_t10_orpheus_max_new_tokens.py)
