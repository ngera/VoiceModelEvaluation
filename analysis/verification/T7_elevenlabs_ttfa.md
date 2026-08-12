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

## Result (three sessions across 4 days, S3 with concurrent ping baseline)

Session 3 added 2026-08-12 in response to external-review item 23
(ISP-confound risk). Ran alongside a concurrent ping-to-1.1.1.1
baseline (274 probes during the S3 window).

| metric | S1 (2026-08-09) | S2 (2026-08-11) | S3 (2026-08-12) | range |
|---|---|---|---|---|
| p50 TTFA | 439 ms | 424 ms | **694 ms** | 424–694 (+64%) |
| p90 TTFA | 479 ms | 469 ms | **816 ms** | 469–816 (+74%) |
| min TTFA | ~410 ms | 403 ms | 605 ms | 403–605 |
| max TTFA | ~510 ms | 683 ms | 2229 ms | 510–2229 |
| n_with_ttfa | 50 | 40 (10 spend-capped) | 40 (10 spend-capped) | — |

**Concurrent ping baseline during S3** (Cloudflare 1.1.1.1, 274 probes):
p50 = 8 ms, p90 = 12 ms, max = **29 ms**, stdev = 3.2 ms, 0 errors.
Local ISP was clean — the S3 slowdown is not last-mile jitter.

## Verdict (updated after S3)

**Confirmed faster than OpenAI (all 3 sessions). Stability
sub-finding REFUTED.**

- Ranking: ElevenLabs stayed faster than OpenAI in every session
  (439/424/694 vs 736/936/1369 on p50). Rank preservation is
  portable.
- Speed: sub-500 ms p90 held only in S1 and S2 (479, 469). **S3's
  816 ms p90 refutes the "reliably clears sub-500 ms" claim** the
  earlier 2-session read had made.
- Stability: p50 range 424–694 ms across 3 sessions = **+64%
  session-to-session movement**, similar magnitude to OpenAI's
  +86% movement on the same 3 dates. The prior "ElevenLabs is
  stable, OpenAI is variable" framing was two-session coincidence.

**What can be published:** ElevenLabs Flash is consistently faster
than OpenAI on our measurements. Absolute TTFA varies substantially
session-to-session (50-90% range) — for a real deployment plan, do
your own multi-session characterisation on your target region.

## Notes for memo / paper

- **The published "stability is a distinct axis" finding was
  refuted by S3** — full retraction in
  [06_KEY_FINDINGS.md § F-11](../../documentation/06_KEY_FINDINGS.md#f-11-retraction-of-the-latency-stability-is-a-distinct-axis-finding).
- **What the retraction demonstrates** (the actual value of this
  test as a portfolio artefact): two-session agreement is a weak
  signal even when the numbers look identical. A third session
  costs pennies and hours — worth it before publishing any
  "stable" claim.
- **ISP is ruled out** as the driver by the concurrent Cloudflare
  ping baseline: 8/12/29 ms p50/p90/max during S3, 0 errors on 274
  probes.
- **The spend cap tripped early on S2 and S3** (40 of 50 trials
  landed) because per-trial cost is higher than pricing.yaml
  estimated. 40 trials still gives tight percentile estimates.
- **Absolute TTFA is D-G disclosed** (residential Windows 11 upper
  bound). Even so, the pattern of session-to-session variance is
  worth its own line in the memo.

## Evidence artefacts

- S1: `analysis/latency-20260809T214106Z/latency.json`
- S2: `analysis/latency-20260811T183202Z/latency.json`
- **S3 (with ping baseline)**: `analysis/latency-20260812T191323Z/latency.json`
- **Ping baseline log**: `runs/ping-baseline-20260812T191138Z.jsonl`
- Ping-baseline runner: [`scripts/latency_with_ping.py`](../../scripts/latency_with_ping.py)
