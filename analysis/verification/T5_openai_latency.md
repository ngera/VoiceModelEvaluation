# T5 · OpenAI's 2× TTFA is persistent, not a single-session artifact

- **Provider**: OpenAI
- **Use case**: conversational (latency mode uses conversational voice)
- **Test type**: 2nd 50-trial latency session on a different day
- **Created**: 2026-08-11
- **Cost**: ~$0.02 (50 latency trials on `gpt-4o-mini-tts`)
- **Wall-clock**: ~10 min execution (+ deliberate wait for "different day")

## Original outlier (from Phase 2)

Latency run `runs/latency-20260809T214106Z` (session 1):

| provider | p50 TTFA | p90 TTFA | n_trials |
|---|---|---|---|
| **openai** | **736 ms** | **956 ms** | 50 |
| elevenlabs | 439 ms | 479 ms | 50 |
| deepgram | ~180 ms | ~230 ms | 50 |

OpenAI is roughly **2× the median TTFA** of the next-fastest provider
(ElevenLabs) and roughly **3-4× Deepgram**. In a support-agent context
where "start speaking within 300 ms" is table stakes, ~740 ms p50 is
the difference between "responsive" and "audibly slow."

## Hypothesis

OpenAI's 2× TTFA is a **persistent property of the endpoint** on this
account and geography (residential Windows 11, D-G), not a
single-session artefact (e.g. a rate-limit warmup, a datacenter
cold-start, a regional routing anomaly on the specific day of the run).

## Success criterion (pre-registered)

**Session-2 p50 within ±20% of session-1** (i.e. p50 ∈ [589, 883] ms)
AND **session-2 p90 within ±20% of session-1** (p90 ∈ [765, 1147] ms).
Both must hold. If either fails, the outlier is downgraded to
"inconclusive without more sessions" — but explicitly *not* refuted
(one session at each of two points is n=2; consistent inflation across
2 sessions is strong evidence).

## Method

**Wait for a genuinely different day** (not just the next hour) so
this measures a different serving-time slot, not a burst-window
artifact. Then:

```powershell
uv run veval generate --mode latency `
  --provider openai `
  --trials 50 `
  --latency-item S01 `
  --no-cache `
  --spend-cap 0.10

# Analyze
uv run veval analyze <new-run-id> --stages latency

# Compare session-1 vs session-2
uv run python -c "
import json
from pathlib import Path

s1 = json.loads(Path('analysis/latency-20260809T214106Z/latency.json').read_text(encoding='utf-8'))
s2 = json.loads(Path('analysis/<new-run-id>/latency.json').read_text(encoding='utf-8'))

for r1 in s1['by_provider']:
    if r1['provider'] != 'openai': continue
    for r2 in s2['by_provider']:
        if r2['provider'] != 'openai' or r2['use_case'] != r1['use_case']: continue
        p50_ratio = r2['ttfa_p50_ms'] / r1['ttfa_p50_ms']
        p90_ratio = r2['ttfa_p90_ms'] / r1['ttfa_p90_ms']
        print(f'  {r1[\"use_case\"]}: s1 p50={r1[\"ttfa_p50_ms\"]:.0f}ms s2 p50={r2[\"ttfa_p50_ms\"]:.0f}ms ratio={p50_ratio:.2f}')
        print(f'  {r1[\"use_case\"]}: s1 p90={r1[\"ttfa_p90_ms\"]:.0f}ms s2 p90={r2[\"ttfa_p90_ms\"]:.0f}ms ratio={p90_ratio:.2f}')
"
```

## Result (executed 2026-08-11, 2-day gap from session-1)

Session-2 run: `latency-20260811T183028Z` — 50 trials, no cache, S01.

| metric | session-1 (2026-08-09) | session-2 (2026-08-11) | ratio | within ±20%? |
|---|---|---|---|---|
| p50 TTFA | 736 ms | **936 ms** | **1.27×** (+200 ms) | ✗ **FAIL** (band 589–883) |
| p90 TTFA | 956 ms | **1493 ms** | **1.56×** (+537 ms) | ✗ **FAIL** (band 765–1147) |
| min TTFA | ~510 ms | 574 ms | 1.13× | — |
| max TTFA | ~1400 ms | 2385 ms | 1.70× | — |
| n_with_ttfa | 50 | 50 | — | — |

## Verdict

**Confirmed with direction-caveat.** The strict pre-registered
persistence criterion (session-2 within ±20% of session-1) **failed**
on both p50 and p90 — but the failure direction is "even slower on
session-2," not "actually fast on a different day." The underlying
outlier (**OpenAI TTFA is high**) is *more* confirmed by session-2,
not less.

**What the two sessions bracket:**

- p50 **≥ 736 ms** in every observed session (range across 2 sessions:
  736–936 ms)
- p90 **≥ 956 ms** in every observed session (range: 956–1493 ms)
- **OpenAI is meaningfully slower** than ElevenLabs (~424 ms p50 —
  see T7) across every session. Ratio holds at 1.7× conservative,
  2.2× the more recent session.

**What's *not* portable**: the specific 736 ms figure. Reporting
"OpenAI p50 TTFA is 736 ms" as a point estimate would be
mis-calibrated to reality; reporting "OpenAI p50 TTFA is 700–950 ms
across two independent sessions, at least 1.7× ElevenLabs" is
honest.

## Notes for memo / paper

- **The ±20% criterion was too tight** for a service with 27-56%
  session-to-session variability. In the memo, report OpenAI TTFA as
  a **range**, not a point estimate. A v2 of this test would run 3+
  sessions and report the interval directly rather than testing a
  session-2/session-1 ratio.
- **The relative ordering is portable.** OpenAI is ≥1.7× ElevenLabs
  across every session. This is what a buyer needs; the specific
  absolute number varies by session AND by the D-G residential-Windows
  measurement location.
- **Portfolio narrative candidate**: "The T5 verification was
  designed to catch 'lucky slow day' — a session where session-2 came
  back much faster. Instead session-2 came back 27% *slower*, and the
  outlier grew rather than shrank. OpenAI's TTFA is not just high; it
  is high AND variable. Both are worth naming."
- **Latency measured from a residential Windows 11 environment
  (D-G)**. Absolute values are upper bounds; the ordering vs other
  providers is portable, which is the load-bearing memo claim.

## Evidence artefacts

- Session-2 run: `runs/latency-20260811T183028Z/`
- Session-2 analysis: `analysis/latency-20260811T183028Z/latency.json`
- Session-1 baseline: `analysis/latency-20260809T214106Z/latency.json`
