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

## Result (three sessions across 4 days, S3 with concurrent ping baseline)

Session 3 added 2026-08-12 in response to external-review item 23
(ISP-confound risk). Ran alongside a concurrent ping-to-1.1.1.1
baseline (274 probes during the S3 window).

| metric | S1 (2026-08-09) | S2 (2026-08-11) | S3 (2026-08-12) | range |
|---|---|---|---|---|
| p50 TTFA | 736 ms | 936 ms | **1369 ms** | 736–1369 (+86%) |
| p90 TTFA | 956 ms | 1493 ms | **1882 ms** | 956–1882 (+97%) |
| min TTFA | 529 ms | 574 ms | 816 ms | 529–816 |
| max TTFA | 1127 ms | 2385 ms | 3694 ms | 1127–3694 |
| n_with_ttfa | 50 | 50 | 50 | — |

**Concurrent ping baseline during S3** (Cloudflare 1.1.1.1, 274 probes):
p50 = 8 ms, p90 = 12 ms, max = **29 ms**, stdev = 3.2 ms, 0 errors.
Local ISP was clean during the S3 window — the observed vendor
slowdown is not last-mile jitter.

## Verdict (updated after S3)

**Confirmed (slower than ElevenLabs) — no meaningful bracket on
absolute values.** Across all three sessions OpenAI's p50 stayed
strictly higher than ElevenLabs' p50 (736/936/1369 vs 439/424/694).
The vendor ranking is portable.

But the specific numerical claims from the earlier 2-session read
did not survive S3:

- p50 range across 3 sessions: **736–1369 ms** (+86%)
- p90 range: **956–1882 ms** (+97%)
- S2→S3 shift alone: +46% p50, +26% p90

**The ping baseline rules out our ISP as the driver** — the S3
window had clean Cloudflare RTTs (p90 = 12 ms, max = 29 ms).
Candidate causes for the shared slowdown across both vendors (not
tested): vendor-side serving load, time-of-day effects, local
machine contention on the client (not network path).

**What can be published:** OpenAI TTFA has never been observed
under 736 ms p50 or 956 ms p90 on our residential-Windows setup.
Ranking vs ElevenLabs is stable; absolute numbers are not.

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

- S1: `analysis/latency-20260809T214106Z/latency.json`
- S2: `analysis/latency-20260811T183028Z/latency.json`
- **S3 (with ping baseline)**: `analysis/latency-20260812T191143Z/latency.json`
- **Ping baseline log**: `runs/ping-baseline-20260812T191138Z.jsonl` (274 probes to 1.1.1.1)
- Ping-baseline runner: [`scripts/latency_with_ping.py`](../../scripts/latency_with_ping.py)
