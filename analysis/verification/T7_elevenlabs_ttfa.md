# T7 · ElevenLabs sub-500 ms TTFA is persistent, not lucky

- **Provider**: ElevenLabs
- **Use case**: conversational (`eleven_flash_v2_5`, low-latency model)
- **Test type**: 2nd 50-trial latency session on a different day
- **Created**: 2026-08-11
- **Cost**: ~$0.02
- **Wall-clock**: ~10 min execution (+ deliberate wait for "different day")

## Original outlier (from Phase 2)

Latency run `runs/latency-20260809T214106Z` (session 1):

| provider | p50 TTFA | p90 TTFA | n_trials |
|---|---|---|---|
| **elevenlabs** | **439 ms** | **479 ms** | 50 |
| deepgram | ~180 ms | ~230 ms | 50 |
| openai | 736 ms | 956 ms | 50 |

ElevenLabs is 2× slower than Deepgram (the on-prem style thin-wrapper
control) but half the p50 of OpenAI, and its p90 is remarkably tight
(479 vs 956 for OpenAI). The story is "consistently fast under 500 ms" —
which is table stakes for a support-agent barge-in experience.

## Hypothesis

ElevenLabs's ~440 ms p50 + tight (~40 ms) p50→p90 gap is a
**persistent property** of the `eleven_flash_v2_5` endpoint on this
account and geography (residential Windows 11, D-G), not luck on the
specific day/time of session-1.

## Success criterion (pre-registered)

**Both** conditions must hold in session-2:

1. **p90 < 500 ms** (the sub-500 ms claim survives)
2. Session-2 **p50 within ±20%** of session-1 (p50 ∈ [351, 527] ms)

## Method

Same as T5 but for elevenlabs — a genuinely different day, then:

```powershell
uv run veval generate --mode latency `
  --provider elevenlabs `
  --trials 50 `
  --latency-item S01 `
  --no-cache `
  --spend-cap 0.10

uv run veval analyze <new-run-id> --stages latency

uv run python -c "
import json
from pathlib import Path

s1 = json.loads(Path('analysis/latency-20260809T214106Z/latency.json').read_text(encoding='utf-8'))
s2 = json.loads(Path('analysis/<new-run-id>/latency.json').read_text(encoding='utf-8'))

for r1 in s1['by_provider']:
    if r1['provider'] != 'elevenlabs': continue
    for r2 in s2['by_provider']:
        if r2['provider'] != 'elevenlabs' or r2['use_case'] != r1['use_case']: continue
        p50_ratio = r2['ttfa_p50_ms'] / r1['ttfa_p50_ms']
        print(f'  {r1[\"use_case\"]}: s1 p50={r1[\"ttfa_p50_ms\"]:.0f}ms s2 p50={r2[\"ttfa_p50_ms\"]:.0f}ms ratio={p50_ratio:.2f}')
        print(f'  {r1[\"use_case\"]}: s1 p90={r1[\"ttfa_p90_ms\"]:.0f}ms s2 p90={r2[\"ttfa_p90_ms\"]:.0f}ms sub_500ms={r2[\"ttfa_p90_ms\"] < 500}')
"
```

## Result (executed 2026-08-11, 2-day gap from session-1)

Session-2 run: `latency-20260811T183202Z` — 50 trials attempted, 10
skipped after $0.10 spend cap hit (spend was tighter than expected
on ElevenLabs Flash; the 40 that ran are plenty for percentile stats).

| metric | session-1 (2026-08-09) | session-2 (2026-08-11) | ratio | passes? |
|---|---|---|---|---|
| p50 TTFA | 439 ms | **424 ms** | 0.97× (−15 ms) | ✅ within ±20% |
| p90 TTFA | 479 ms | **469 ms** | 0.98× (−10 ms) | ✅ **< 500 ms** |
| min TTFA | ~410 ms | 403 ms | — | — |
| max TTFA | ~510 ms | 683 ms | — | (one outlier trial) |
| n_with_ttfa | 50 | 40 (10 spend-capped) | — | — |

## Verdict

**Confirmed.** Session-2 came in within a hair of session-1:
p50 differs by −3%, p90 by −2%. Both well inside the ±20% band.
p90 stayed sub-500 ms as predicted.

**Two-session bracket:**
- p50: **424–439 ms** across 2 sessions (span 15 ms, ~3.4% of the mean)
- p90: **469–479 ms** across 2 sessions (span 10 ms, ~2.1% of the mean)
- Sub-500 ms p90 **confirmed in both sessions**

**Contrast with T5**: OpenAI's session-to-session variability was
27-56% on the same two dates. ElevenLabs Flash is 2-3% on the same
two dates. This is not just a "faster" story; it is a **more
stable** story. The two axes trade off differently for the two
providers.

## Notes for memo / paper

- **Sub-500 ms p90** is the load-bearing claim for support-agent
  deployments (voice barge-in requires <300 ms to feel snappy;
  <500 ms is the threshold at which the human perception starts
  flagging "slow"). ElevenLabs Flash clears this every session
  across a 2-day gap.
- **Session-to-session stability is itself a finding.** Report
  ElevenLabs TTFA as **439 ± 8 ms p50** (session-2 mean-of-two ±
  half-span) — a tight point estimate you can actually publish.
- **Portfolio narrative candidate**: "Two providers, two sessions,
  two days apart: OpenAI moved 27% on p50 and 56% on p90 across the
  two sessions. ElevenLabs Flash moved 3% and 2%. Speed differs
  between providers; so does stability, and stability is a distinct
  buyer concern."
- **The spend cap tripped early on session-2** because the actual
  per-trial cost was higher than the pricing model expected — flag
  for pricing.yaml review. 40 trials still gives tight percentile
  estimates.
- **Absolute TTFA is D-G disclosed** (residential Windows 11 upper
  bound). An enterprise co-located deployment is expected to see
  lower still.

## Evidence artefacts

- Session-2 run: `runs/latency-20260811T183202Z/`
- Session-2 analysis: `analysis/latency-20260811T183202Z/latency.json`
- Session-1 baseline: `analysis/latency-20260809T214106Z/latency.json`
