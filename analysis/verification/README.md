# Phase 2c · Outlier verification pack

Scaffolded 2026-08-11 after Phase 2b F-8 findings reshuffled the
original roster (runbook v2 §2c). Each `T{N}.md` / `N{N}.md` file
contains its own hypothesis, success criterion, method, and result
sections. Fill result + verdict after execution.

## Roster

| # | Provider | Type | Cost | Wall-clock | Can do now? |
|---|---|---|---|---|---|
| [T1](T1_cartesia_clipping.md) | Cartesia | Downgraded write-up | $0 | 5 min | **✅ done — verdict Confirmed** |
| [T2](T2_orpheus_wer.md) | Orpheus | Manual listen 10 items | $0 | 20 min | ✅ (headphones + reference) |
| [T4](T4_elevenlabs_L03_fadeout.md) | ElevenLabs | Regen L03 × 3 + drift | $0.02 | 2 min | ✅ (fresh calls) |
| [T5](T5_openai_latency.md) | OpenAI | 2nd 50-trial latency session | $0.02 | 10 min | ⏸ **needs different day** |
| [T6](T6_speechify_voice_bias.md) | Speechify | 20 items × alt Simba voice | $0.20 | 15 min | ✅ (alt voice ID needed first) |
| [T7](T7_elevenlabs_ttfa.md) | ElevenLabs | 2nd 50-trial latency session | $0.02 | 10 min | ⏸ **needs different day** |
| [T8](T8_orpheus_cost.md) | Orpheus | 10 long-item cost measurement | $0.05 | 15 min | ✅ + Replicate dashboard |
| [N1](N1_openai_narration_inversion.md) | OpenAI | Manual listen 5 narr items | $0 | 10 min | ✅ (headphones) |
| [N2](N2_fish_conv_dnsmos.md) | Fish | Spot listen 3 + noise floor | $0 | 10 min | ✅ (headphones + query) |

**Retired**: T3 (Orpheus PQ artefact) — answered by 2b F-8. See
[RESEARCH_LOG.md](../../documentation/RESEARCH_LOG.md) F-9.

## Suggested order

1. **Today** (all doable now): T1 already done · T4 (fresh regen, 2 min) ·
   T6 (needs alt voice lookup first) · T8 (Replicate dashboard access) ·
   T2 + N1 + N2 (manual listen — batch through with headphones)
2. **Tomorrow** (different day needed): T5 + T7 (2nd latency sessions)

## Design principles (from runbook v2 §2c)

1. Hypothesis + falsifiable criterion **before** execution
2. Fresh calls (no cache) where regeneration is required
3. Winners get the same scrutiny as losers
4. Verdict is **Confirmed / Refuted / Inconclusive** (three
   outcomes, not two)
5. Per-test artefact so the paper's supplementary materials link
   directly to raw evidence
