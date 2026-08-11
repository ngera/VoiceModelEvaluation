# T1 · Cartesia clipping is systemic gain-staging (DOWNGRADED)

- **Provider**: Cartesia
- **Use cases**: conversational + narration
- **Test type**: write-up only — no regeneration
- **Created**: 2026-08-11
- **Status**: DOWNGRADED from original "regen 20 items" per Phase 2b F-4a
  finding. Two independent pipelines already corroborate.

## Original outlier (from Phase 2)

Hygiene analyzer on `campaign-20260809T204608Z`: Cartesia flagged with
**429 clipped samples (conversational) / 406 clipped samples
(narration)** — roughly **100× the next-worst provider**. See
`analysis/campaign-20260809T204608Z/hygiene.json`, `by_provider` rows
for cartesia.

## Original hypothesis

Cartesia's mastering pipeline runs *at peak* by design (zero-headroom
gain staging) rather than the −1 dBFS or −0.3 dBFS ceiling most TTS
providers leave. This produces:
1. A clipping rate one to two orders of magnitude above other providers
2. Peak amplitudes right at or above ±1.0 in the float representation
3. A signal-cleanliness penalty on downstream MOS predictors that key
   off peak headroom

## Success criterion (pre-registered)

Downgrade: cite the independent Phase 2b DNSMOS refusal evidence as
second-pipeline corroboration; no fresh regen required.

## Phase 2b evidence (independent corroboration)

`speechmos.dnsmos` runs on ONNX and refuses any input where
`peak_abs > 1.0`, raising `ValueError: np.ndarray values must be
between -1 and 1`. Our wrapper classifies this as
`input_peak_out_of_range` with the observed peak_abs attached.

Refusal counts on `campaign-20260809T204608Z` (n=75 per cell):

| provider | use_case | DNSMOS refused | % refused | others refused |
|---|---|---|---|---|
| **cartesia** | conversational | **32** | **43%** | 0 |
| **cartesia** | narration | **37** | **49%** | 0 |
| google | narration | 4 | 5% | — |
| all others (13 cells) | — | 0 | 0% | — |

Two independent code paths (hygiene `peak_dbfs` computed from raw
samples + speechmos ONNX inference refusing to run) flag the same
8-of-8 provider unanimously.

**Reinforcing sub-finding (N4):** even on the *surviving* 38/75
Cartesia narration items (those DNSMOS *did* score), Cartesia ranks
**#8 / #8 / #8** on OVRL / SIG / BAK — the three-scale P.835 MOS. So
the clipping isn't the whole story; the mastering signature is also
worst on speech-signal cleanliness on the non-refused subset.

## Result

**Confirmed.** Cartesia's mastering is systemically peak-bound and
this is not a batch artifact:

- Two independent measurement pipelines (hygiene sample-clipping
  detection + speechmos ONNX inference refusal) flag the same
  provider at ~1-2 orders of magnitude above the next-worst — no
  other provider shows either signal at a comparable rate
- ~46% of Cartesia's output (average across the two use cases) is
  literally unscorable by a standard MOS predictor because of peak
  values ≥1.0
- The surviving 38 narration items still rank #8 on all three P.835
  axes — the mastering choice affects the full waveform, not just
  the peaks

## Verdict

**Confirmed** — systemic gain-staging choice at the provider level.

## Evidence artifacts

- `analysis/campaign-20260809T204608Z/hygiene.json` — original clipping
  counts (429/406 samples)
- `analysis/campaign-20260809T204608Z/quality.json` —
  `dnsmos_by_provider` (n_valid=43+38 for cartesia, 75 for all others)
  and file-level `dnsmos_error` fields
- `documentation/06_KEY_FINDINGS.md` F-4a and F-9 (T1 row)
- `configs/analyzers.yaml` `dnsmos_error_policy` (documented amendment)

## Notes for memo / paper

- This is the **cleanest independent-corroboration story** the
  project has: two pipelines, non-overlapping code, both flag
  unanimously. Worth its own paragraph in §8.
- Cartesia is technically Audiobox mid-pack on narration (rank #3
  PQ). "Cartesia sounds fine but the file is broken for anything
  downstream" is the memo one-liner.
- Actionable disclosure: for anyone rebuilding on Cartesia, apply
  −1 dBFS peak limit *before* handing the audio to any MOS
  predictor or ASR that resamples (the resample filter ringing is
  what pushes borderline peaks over 1.0).
