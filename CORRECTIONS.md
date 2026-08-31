# CORRECTIONS.md — retracted claims across all review rounds

*One dated row per retracted claim. Each row names the original
assertion, the artefact that falsified it, and the commit that
retracted it. This file is the audit trail; the numbered reports
themselves (01-07 in `documentation/`) read as final reports, with
no inline "prior drafts said X" narrative.*

---

## What lives here vs elsewhere

- **CORRECTIONS.md** (this file) — every retracted assertion,
  dated and traceable to a git commit + a source artefact
- **DEVIATIONS.md** — pre-registered *amendments* made before
  results existed (e.g., roster extension 6→8, WER-threshold
  refinement). Deviations are decisions the campaign then
  honoured. Corrections are claims the results then falsified.
  Different things.

---

## Retracted claims

Rows are numbered in the order they were logged; the "Round" column
records which external-review round (R1..R6, ordered chronologically)
surfaced the retraction. R1-R2 rows below are backfilled from git
history — earlier rounds pre-dated this file's creation but produced
retractions worth recording for completeness.

| # | Round | Original assertion | What retracted it | Artefact | Retraction commit |
|---|---|---|---|---|---|
| B1 | R1 | "ElevenLabs Flash is not just faster — it's more predictable" / "Stability is a distinct vendor axis" (05 §3 headline, 04 latency, T5/T7 verdicts). The project's showcase reversal. | Third latency session (2026-08-12, with concurrent Cloudflare-1.1.1.1 ping baseline) showed BOTH vendors moved 50-90% p50 across three sessions; two-session agreement was coincidence. The ping baseline was clean (p50=8 ms, p90=12 ms, 0 errors on 274 probes), ruling out the ISP-jitter hypothesis. | `analysis/latency-20260812T191143Z/latency.json` (OpenAI S3), `analysis/latency-20260812T191323Z/latency.json` (ElevenLabs S3), `analysis/ping-baseline-20260812T191138Z.jsonl` | `2e77111` (Wave 2 tie verdicts) → `a2baebb` (F-11 rewrite) |
| B2 | R1 | "0.035 noise floor" (single-number heuristic applied across two different signal scales for adjudicating between-vendor differences) | Recomputed per-vendor per-signal SE(diff) = √(SE_a² + SE_b²) with SE_i = SD(vendor's 75-item column) / √75. The pooled 8-vendor recompute is the reproducible ground truth in `scripts/_noise_floor_recompute.py`. | `analysis/campaign-20260809T204608Z/quality.json` + `scripts/_noise_floor_recompute.py` | `2e77111` |
| B3 | R2 | "5 Confirmed" verification pack tally (headline verdict summary in 04) | Actual verdict distribution: 3 Confirmed cleanly (T1, T7, N2), 3 Confirmed with refinement/reversal (T4, T5, T6), 1 Answered by another test (T2 → T8), 1 Refuted with a bigger finding (T8), 1 Retired mid-project (T3), 1 Pending manual (N1). "5 Confirmed" collapsed six categories to one. | `analysis/verification/README.md` + individual test verdict files | `2e77111` |
| B4 | R2 | "~40% of load-bearing findings" changed after verification (or a similar aggregate share claim in the case study) | Never held up under a precise definition of "load-bearing." The verification pack's honest tally (the 4 categories in row B3) is the load-bearing report, and every headline finding that changed is named individually (T4/T5/T6/T7/T8/F-11), not aggregated as a percentage. | `analysis/verification/README.md` | `2e77111` |
| B5 | R2 | "Three independent pipelines" (F-4 corroboration for Cartesia clipping) | Two code paths, not three: sample-level peak detection in the hygiene analyzer (numpy peak scan) + DNSMOS's peak-out-of-range refusal. The manual acoustic-listen was scoped out (n=1 rater problem, D-H). | `analysis/campaign-20260809T204608Z/hygiene.json` (`clipped_samples`) + DNSMOS refusal counts in `analysis/campaign-20260809T204608Z/quality.json` (`n_dnsmos_errors`) | `2e77111` |
| 1 | R3 | "Deepgram TTFA ~180 ms p50 / ~230 ms p90" (T5, T7, 04 footnote ³, 05 Q1) | Actual measurement is 583/674 (S1a) and 564/670 (S1b) — no run measures Deepgram under 500 ms | `analysis/latency-20260809T214106Z/latency.json` and `latency-20260809T222356Z/latency.json` | `f6e3a7d` |
| 2 | R3 | "Cartesia p90 unmeasured / — in latency table" | Cartesia p90 was measured at 529 / 530 ms in S1a / S1b | `analysis/latency-20260809T*/latency.json` | `f6e3a7d` |
| 3 | R3 | "ttfa_p90_ms < 400 gate: 2 pass / 2 fail among 4 measured" | Every measured streaming vendor fails the gate (best measurement: ElevenLabs 469 ms p90 in S2; all others worse) | `analysis/latency-*/latency.json` + `configs/gates.yaml` | `f6e3a7d` |
| 4 | R3 | "Real-time-voice recommendation: sub-500 ms perception threshold as the pre-committed bar" | The pre-registered gate is `ttfa_p90_ms < 400`, not 500. The 500 ms figure is the perception-threshold reference from spec A.1. Both are now named explicitly. | `configs/gates.yaml` | `f6e3a7d` |
| 5 | R4 | "Orpheus $0.030/1K words is cheapest overall" (04 Q2, 05 Q2, 06 F-3, 06 F-5) | The $0.030 is a `cost_model.py` output under a 100-word-per-call default that predates T8's measured per-call output (~35 words). Honest per-1K-words is ~$0.067-0.088 — peer-priced to OpenAI's $0.075. | `src/veval/analyze/cost.py` line 177 + T8 measurements in `analysis/verification/T8_orpheus_cost.md` | `b0fc7fa` |
| 6 | R4 | "9.5σ Speechify vs Orpheus is a truncation artifact" | Orpheus per-stratum AB.PQ means (short 8.008 / medium 7.974 / long 8.009) are essentially identical — truncation does not depress score. The 9.5σ is a real per-call rendering effect; Orpheus should be excluded on Q1 grounds (14.59-s cap ≠ narration workflow), not statistical artifact. | `analysis/campaign-20260809T204608Z/quality.json` | `b0fc7fa` |
| 7 | R4 | "Every marked-¹ cell was computed on structurally incomplete audio" + "~16% of expected duration" | 27 of 75 Orpheus narration files are truncated (36%), not "every"; 48 are complete. Overall mean duration is 10.05 s vs Speechify 16.09 s = ~58% delivered, not 16%. | `analysis/campaign-20260809T204608Z/hygiene.json` | `8451e0f` |
| 8 | R4 | "144 items with valid reference transcripts / 6,651 words" | 150 items, 6,741 words, 38,916 chars (verified from `wer.json`; original "144" was a dedup bug in an ad-hoc counting script that collapsed items with identical wordcount+charcount tuples) | `analysis/campaign-20260809T204608Z/wer.json` | `8451e0f` |
| 9 | R5 | "Audiobox rewards warmth, DNSMOS rewards cleanliness" (F-8 aggregate framing) | Per-pair Spearman ρ: PQ↔DNSMOS mean = +0.238 (agree; +0.571 with p808 is the strongest positive correlation in the matrix). CE↔DNSMOS mean = −0.506. AB.PQ agrees with DNSMOS. The construct-decomposition is within Audiobox, not between pipelines. | `analysis/campaign-20260809T204608Z/cross_metric.json` | `8451e0f` |
| 10 | R5 | AB.PQ column labelled "(warm)" in 04 rankings, glossary described PQ as "rewards warmth, expressiveness, engagement" | PQ is Meta's technical-cleanliness axis; the "warm" label was wrong on the axis carrying the Speechify winner claim | Meta Audiobox Aesthetics paper + `cross_metric.json` correlations | `8451e0f` |
| 11 | R5 | "Speechify @10K/mo = $0.100/1K words" (cost table) | cost_model.json has $1.000/1K at 10K/mo — a 10× table-entry error. At 10K/mo Speechify is #7 of 8 on cost. | `analysis/campaign-20260809T204608Z/cost_model.json` | `8451e0f` |
| 12 | R5 | "Primary campaign cost ~$50 / total project spend ~$56" | Actual campaign cost is $7.85 (from `total_observed_cost_usd`). Total measured project spend across all committed cost_model.json files is ~$12.60. The ~$50 / ~$56 figures were pre-project planning estimates from spec §8 carried into publication as if metered. | `analysis/*/cost_model.json` `total_observed_cost_usd` fields | `8451e0f` |
| 13 | R5 | "Low variance under the fixed-length cap" (mechanism for Orpheus narration SD) | Orpheus conv AB.PQ SD is 0.2731 (2nd HIGHEST of 8) under identical truncation. Direct falsification of the "cap depresses variance" mechanism. | `analysis/campaign-20260809T204608Z/quality.json` | `8451e0f` |
| 14 | R5 | "−78.7 dBFS is mostly silence padding the truncated clips out" | Orpheus narration `speech_ratio` = 0.901, higher than Speechify's 0.875. Clips are 90% speech, not silence. The quiet noise floor is a real Orpheus property. | `analysis/campaign-20260809T204608Z/hygiene.json` | `8451e0f` |
| 15 | R5 | "5 conversational gates: `ttfa_p90_ms`, `failure_incidence_pct`, `clipped_samples`, `acoustic_noise_floor_dbfs`, `commercial_use_permitted`" | `configs/gates.yaml` has 4 conversational gates, not 5. The `acoustic_noise_floor_dbfs` gate exists only under narration as `long_stratum_acoustic_noise_floor_dbfs`. | `configs/gates.yaml` | `8451e0f` |
| 16 | R5 | "RTF was not measured in v1" | RTF was measured on every latency-mode trial (per-trial `rtf` field, n=50 per session). Just measured on the wrong workload (2.6-s conversational S01 instead of long narration items). | `analysis/latency-*/latency.json` per-item records | `8451e0f` |
| 17 | R5 | "S1/S2 were on Creator credits, unaffected; only S3 hit the pay-per-1K-chars spend cap" | ElevenLabs S2 was also n=40, not 50. Both S2 and S3 landed 40/50 trials. Mechanism (subscription credit exhaustion vs spend cap) not diagnosed. | `analysis/latency-20260811T183202Z/latency.json` `n_items = 40` | `8451e0f` |
| 18 | R5 | T5/T7 verification files showed only S1a run (~736/956 for OpenAI, ~439/479 for ElevenLabs), collapsing "S1" to a single row | Two same-day S1 runs exist: S1a (T21:41) and S1b (T22:23), both n=50. F-11 now shows all four vendor-session cells per speed-critical vendor, not two — six cells across both vendors, not three sessions. | `analysis/latency-20260809T222356Z/latency.json` | `8451e0f` |
| 19 | R5 | Per-stratum Orpheus AB.PQ table used text-length-derived groupings (53/14/8) inconsistent with the hygiene-strata truncation table above it | Recomputed on hygiene strata directly (short/jargon/edge/probe/medium/long, n = 12/12/8/15/20/8), all in the 7.957–8.088 AB.PQ range. No method drift between adjacent tables. | `analysis/campaign-20260809T204608Z/quality.json` + `hygiene.json` `stratum` field | `b0fc7fa` |
| 20 | R5 | "The 9.5σ→7.0σ shift comes from Orpheus's low variance under the cap" | Speechify SD_75 = 0.0943 (lowest, retained), Orpheus 0.0967 (2nd lowest, excluded), Cartesia 0.1795. The shift is driven by Cartesia's higher SD inflating SE(diff), not by anything about Orpheus's variance. | `analysis/campaign-20260809T204608Z/quality.json` | `8451e0f` |
| 21 | R6 | Three line-wrap-hidden "prior/earlier drafts" narratives survived a phrase-level grep audit (02:313 "0.035 noise floor", 04:550 "9.5σ is a truncation artifact", 06:87 "excluded Google from the leading cluster") | The verification procedure in rule 4 used a phrase-level grep. This corpus hard-wraps at ~70 chars, so a two-word phrase like "Prior drafts" split across a newline as "Prior\ndrafts" returned zero hits. Rule 4 has been upgraded to normalise whitespace before matching (see § How to add to this file below). | The three source files themselves + `documentation/0[1-7]*.md` hard-wrap convention | *(this round)* |

---

## How to add to this file

When a claim in the reports is retracted:

1. Identify the artefact (JSON file, script line, or committed
   config) that falsified it — every entry should be reproducible
   from a `python -X utf8 -c` snippet
2. Add a row to the table above with round, original assertion,
   what retracted it, artefact, and commit SHA
3. **Delete the original assertion from the report.** Do NOT leave
   a "prior drafts said X" note in the report itself — the pattern
   of adding correction narrative next to a corrected number
   (documented as retraction #21 above) is exactly the thing this
   file exists to keep out of the reports. A paraphrase of the
   retracted claim in the report is not fine either.
4. **Verify with the line-wrap-safe check below.** A phrase-level
   `grep -rn` for a two-word retracted phrase misses hard-wrapped
   text (row 21 was three survivors of exactly that blind spot).
   Use whitespace-normalised matching instead:

   ```bash
   python -X utf8 -c "
   import re, glob
   targets = [r'(?i)(prior|earlier)\s+drafts?', r'(?i)retract',
              r'CORRECTIONS\.md', r'F-1[2-9]',
              r'(?i)round[-\s][3-9]', r'(?i)after[-\s]review']
   for f in sorted(glob.glob('documentation/0[1-7]*.md')):
       text = open(f, encoding='utf-8').read()
       for pat in targets:
           for m in re.finditer(pat, text):
               line = text[:m.start()].count(chr(10)) + 1
               snippet = re.sub(r'\s+', ' ',
                                text[max(0,m.start()-30):m.end()+50])
               print(f'{f}:{line}  [{pat}]  ...{snippet}...')
   "
   ```

   Each retracted phrase should return zero hits in
   `documentation/0[1-7]*.md`. Any hit is a live contradiction.
   Add new retracted phrases to the `targets` list as they're
   logged.
