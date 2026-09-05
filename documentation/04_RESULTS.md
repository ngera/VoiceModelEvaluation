# 04 · Results Summary

*Full per-provider measurements across 8 vendors × 2 use cases,
plus the verification-pack verdicts and the cost calculus a
decision-maker needs.*

> **⚠ Scope disclaimer** · Results as of 2026-09-01 on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. No financial
> relationship with any vendor. Not legal/business/purchasing
> advice. Full scope in [../DISCLAIMER.md](../DISCLAIMER.md).

---

## Headline in one line

**No single vendor dominates.** Every vendor with an axis-level top-2
placement loses at least one other axis, and one vendor (Google) has
no top-2 placement on any axis of either use case — a legitimate
"middling generalist" position. The right pick depends on which
axis your listener use case maps to, and on which failure mode you
can absorb. See [05_CASE_STUDY.md](05_CASE_STUDY.md) for the full
narrative and [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md) for the F-8 /
T8 / T5+T7 headline findings.

**Two-phase results structure**: **numbers below are from R2**
(`campaign-20260809T204608Z`, 2026-08-09), which ran fully from
the content-hash cache (see cache-only scope note below). **R3
replication** (`campaign-20260831T175358Z`, 2026-08-31) ran fresh
(`--no-cache`) and adjudicates the RTF gate; per-vendor
R2-vs-R3 deltas per quality axis (12 of 14 top-1 positions
unchanged across 6 quality axes + WER × 2 use cases; per-axis
full-ranking Spearman ρ = 0.905–1.000) live
in [`analysis/round3-vs-round2-comparison.md`](../analysis/round3-vs-round2-comparison.md).
Phase 1 raised three follow-up questions — the F-6 loudness fade
extent, the F-7 voice-swap consistency for non-Speechify vendors,
and F-11's ≥5-session latency variance — that a targeted
**Phase 2 experiment pack** (2026-09-01) answered. Phase 2
additions appear as `Follow-up N` subsections in the relevant
tables and are linked back to the full write-up at
[EXPERIMENTS_2026-09-01.md](EXPERIMENTS_2026-09-01.md). No
Phase 1 number in this document changed as a result; Phase 2
sharpened findings and rewrote F-7's framing (see F-7 for the
retraction), it did not overturn the R2 quality tables.

---

## Full per-provider results

Two quality raters (Meta Audiobox + Microsoft DNSMOS), hygiene
noise-floor, WER via two-judge agreement, latency (conversational
only, 50-trial session), and public-tier cost per 1K words at 100K
words/month.

**Important scope note (single-realization)**: **each cell in
these tables is a single realization** — one draw per (vendor, item)
in the campaign, aggregated over 75 items. F-1 established that no
vendor produces byte-identical output across draws, so every value
here carries an unquantified within-vendor draw component. The
Rankings summary below applies a proper SE(diff) test that
captures the between-item component but not the within-draw
component (which is small for aggregates over 75 items — see the
`SD_within` column in the noise-floor recompute output). For
Orpheus narration + Cartesia DNSMOS narration, the story is
different — see the footnotes on those rows.

**Important scope note (cache-only R2, fresh R3)**: the R2 campaign
run `campaign-20260809T204608Z` **ran fully from the content-hash
cache** — every audio file it "produced" was replayed from bytes
generated at an earlier, unrecorded date. That has two knock-on
effects on R2 alone:

- Latency's `n_fresh = 0` and `n_with_ttfa = 0` for every vendor
  in [`analysis/campaign-20260809T204608Z/latency.json`](../analysis/campaign-20260809T204608Z/latency.json)
  (R2 has no timing data — TTFA comes from the dedicated
  latency-mode sessions instead).
- Combined with F-1 (nothing is byte-reproducible), **each R2 cell
  is a frozen single draw whose exact synthesis date is not
  recorded in `runs/<id>/manifest.json`** — only the cache-hit
  timestamp is. The published-date-on-every-finding discipline
  in 02 is genuine at the *analysis-artefact* level but degrades
  at the *raw-audio-generation* level for cache-hit R2 rows.

**R3 (`campaign-20260831T175358Z`) closes this gap**: it ran with
`--no-cache`, so `n_fresh = 75` and `n_with_total = 75` for every
(vendor, use case) pair except Orpheus conversational (74 / 74;
one call failed silently, see [round3-vs-round2 § footnote 1](../analysis/round3-vs-round2-comparison.md#per-vendor-observed-cost-delta)
and [CORRECTIONS row 30](../CORRECTIONS.md)). That gave the
campaign a fresh generation timestamp per row and populated
`long_stratum_rtf_p50` for all 16 cells — adjudicating the
pre-registered `rtf ≥ 3.0` narration gate for the first time
(5 pass / 3 fail; see [RTF admission](#rtf-admission)
below). All R2 quality-axis and hygiene claims are unaffected —
they read audio bytes, not timestamps — and R3 reproduced them
at **12 of 14 top-1 positions unchanged** (6 quality axes + WER,
each × 2 use cases). The two flips are DN.p808 narration
(Cartesia → Fish) and WER conv (OpenAI → Speechify), both inside
noise-floor bands. Cost is not a replication signal — modelled
cost = chars × rate, and both runs used the same corpus, so cost
matches by construction regardless of what audio came back.

**Colour legend** (per column, direction-normalized):

<table>
<tr>
<td><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="green"></td>
<td>top 2 within the column (best 2 of 8)</td>
</tr>
<tr>
<td><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="yellow"></td>
<td>middle 4 within the column (rank 3–6)</td>
</tr>
<tr>
<td><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="red"></td>
<td>bottom 2 within the column (worst 2 of 8)</td>
</tr>
</table>

For lower-is-better columns (clip samples, noise floor dBFS,
TTFA ms, $/1K words) the colour flips direction — **green = lowest = best**.
For `clip samples`, values of 0 are always green (perfect); any value
≥100 is red regardless of ranking. TTFA cells marked "—" indicate
adapters that don't stream (Speechify, Fish, Google, Orpheus per D-008
and adapter-shape).

**WER % is deliberately not colour-coded.** F-2 documents that
wav2vec2 (the second judge) inflates absolute WER on TTS speech,
and F-3 documents that jiwer's default normaliser drops articles
that both judges heard — those get counted as errors even though
the audio contained them. Painting one vendor's WER cell green
and another's red would imply an absolute pass/fail claim the
data does not support. The numbers are shown for **relative
ranking within the column** only; the glossary makes the same
point.

*Note: GitHub's markdown sanitizer strips cell background colors
(both `style="..."` and the legacy `bgcolor` attribute), so the
color indicators are rendered as inline color-chip images via
[placehold.co](https://placehold.co). If images fail to load, the
alt text ("best" / "mid" / "worst") describes the tier.*

**Source: R2 `campaign-20260809T204608Z` — every cell in the two
tables below.** Verified against both R2 and R3 quality.jsons in
the R30 audit (96 of 96 cells match R2; 24 also match R3 to two
decimals). R3 numbers with per-cell R2→R3 deltas live in
[`analysis/round3-vs-round2-comparison.md`](../analysis/round3-vs-round2-comparison.md).
See also the run-source note at [§ Full per-provider results
scope note](#full-per-provider-results) above.

### Conversational (R2 — `campaign-20260809T204608Z`)

<table>
<thead>
<tr>
<th>Vendor</th>
<th>AB.PQ</th>
<th>AB.CE</th>
<th>DN.p808</th>
<th>DN.ovrl</th>
<th>DN.sig</th>
<th>DN.bak</th>
<th>clip samples</th>
<th>noise floor (dBFS)</th>
<th>WER %</th>
<th>TTFA p50 (ms)</th>
<th>$/1K words</th>
</tr>
</thead>
<tbody>
<tr>
<td><b>speechify</b></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 7.90</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 6.46</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.98</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.30</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.56</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.07</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 1</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> -57.0</td>
<td align="right">14.3</td>
<td align="right">—</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.100</td>
</tr>
<tr>
<td><b>elevenlabs</b></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 7.76</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 5.96</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.12</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.47</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.69</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.18</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -52.0</td>
<td align="right">14.1</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 439</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 0.220</td>
</tr>
<tr>
<td><b>openai</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.74</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.11</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.01</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.49</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.70</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.19</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -52.5</td>
<td align="right">13.7</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 736</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0.075</td>
</tr>
<tr>
<td><b>fish</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.70</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 6.24</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.86</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.15</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.41</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 4.05</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> -39.7</td>
<td align="right">13.8</td>
<td align="right">—</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.075</td>
</tr>
<tr>
<td><b>google</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.62</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.18</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.82</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.27</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.57</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 4.02</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> -33.7</td>
<td align="right">15.1</td>
<td align="right">—</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.150</td>
</tr>
<tr>
<td><b>deepgram</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.62</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.21</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.77</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.31</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.58</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.07</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -46.2</td>
<td align="right">16.6</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 583 <sup>³</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.150</td>
</tr>
<tr>
<td><b>cartesia</b> <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 7.44</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 5.96</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.89 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.25 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.48 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.13 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 406</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> -57.1</td>
<td align="right">16.4</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 467</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 0.160</td>
</tr>
<tr>
<td><b>orpheus</b></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 7.41</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.01</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.87</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.33</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.62</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.10</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -53.2</td>
<td align="right">26.9</td>
<td align="right">—</td>
<td align="right">0.030 <sup>†</sup></td>
</tr>
</tbody>
</table>

### Narration (R2 — `campaign-20260809T204608Z`)

<table>
<thead>
<tr>
<th>Vendor</th>
<th>AB.PQ</th>
<th>AB.CE</th>
<th>DN.p808</th>
<th>DN.ovrl</th>
<th>DN.sig</th>
<th>DN.bak</th>
<th>clip samples</th>
<th>noise floor (dBFS)</th>
<th>WER %</th>
<th>$/1K words</th>
</tr>
</thead>
<tbody>
<tr>
<td><b>speechify</b></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 8.15</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 6.66</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.05</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.42</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.63</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.17</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 5</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -55.2</td>
<td align="right">13.0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.100</td>
</tr>
<tr>
<td><b>orpheus</b> <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 8.00 <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 6.26 <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.06 <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.45 <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.64 <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.21 <sup>¹</sup></td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> -78.7 <sup>¹</sup></td>
<td align="right">27.2</td>
<td align="right">0.030 <sup>†</sup></td>
</tr>
<tr>
<td><b>cartesia</b> <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.99</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.32</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.13 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.20 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.45 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 4.05 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 429</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> -55.3</td>
<td align="right">12.4</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 0.160</td>
</tr>
<tr>
<td><b>google</b> <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.97</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.44</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 4.02 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.35 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.60 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.11 <sup>²</sup></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 39</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> -36.8</td>
<td align="right">13.0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.150</td>
</tr>
<tr>
<td><b>elevenlabs</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.93</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 6.47</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.05</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.34</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.61</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 4.07</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> -41.5</td>
<td align="right">12.8</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 0.220</td>
</tr>
<tr>
<td><b>deepgram</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.86</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.40</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.07</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.44</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.68</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.15</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -46.8</td>
<td align="right">13.5</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.150</td>
</tr>
<tr>
<td><b>fish</b></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 7.63</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.31</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.12</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.40</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.67</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.10</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -46.6</td>
<td align="right">14.0</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0.075</td>
</tr>
<tr>
<td><b>openai</b></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 7.62</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 6.18</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.98</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.46</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 3.68</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 4.18</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> -54.5</td>
<td align="right">13.3</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 0.075</td>
</tr>
</tbody>
</table>

Rows sorted by AB.PQ (Audiobox production_quality) descending. See
[Glossary](#glossary) for column definitions and
[scripts/_color_code_tables.py](../scripts/_color_code_tables.py) for
the ranking rules.

**Footnote ¹ (Orpheus narration)**: Orpheus's narration output is
truncated to exactly **14.59 seconds per call** by the model's
hard output cap (F-9 T8, stdev 0.000s across the 8 long items
tested). Actual truncation scope, per
`analysis/campaign-20260809T204608Z/hygiene.json` (using
`total_seconds > 14.55` as the truncation flag):

| Stratum | n | mean duration (s) | max (s) | truncated |
|---|---:|---:|---:|---:|
| long | 8 | 14.59 | 14.59 | **8 (all)** |
| medium | 20 | 14.45 | 14.59 | **18** |
| probe | 15 | 8.99 | 14.59 | 1 |
| edge | 8 | 10.84 | 12.97 | 0 |
| jargon | 12 | 7.39 | 8.36 | 0 |
| short | 12 | 3.17 | 4.10 | 0 |
| **Full narration column** | 75 | 10.05 | 14.59 | **27 / 75 (36%)** |

**27 of 75 narration files are truncated (36%); 48 are rendered
complete.** Overall Orpheus narration mean duration is 10.05 s vs
Speechify 16.09 s vs ElevenLabs 17.36 s — Orpheus delivered ~58%
of what Speechify delivered on the same corpus. Truncation counts
in the table above are from actual measured audio duration
(hygiene.json `total_seconds`), which is authoritative for this
question.

**Orpheus CONV is also truncated: 25 / 75 files > 14.55 s.** The
conversational per-vendor table above does not currently carry a
truncation footnote — symmetric-scrutiny gap logged in
[07 § "One voice per vendor per use case"](07_GAPS_AND_FUTURE_WORK.md#2-one-voice-per-vendor-per-use-case-partially-closed-by-phase-2),
not fixed in v1.

**Per-hygiene-stratum Orpheus AB.PQ + DNSMOS narration means**
(computed from `analysis/campaign-20260809T204608Z/quality.json`
using the `stratum` field from `hygiene.json` — the same grouping
as the truncation table above, no method drift):

| hygiene stratum | n | mean audio duration | truncated | AB.PQ mean | AB.PQ SD | DN.OVRL mean |
|---|---:|---:|---:|---:|---:|---:|
| short | 12 | 3.17 s | 0 / 12 | 7.957 | 0.101 | 3.380 |
| jargon | 12 | 7.39 s | 0 / 12 | 7.999 | 0.114 | 3.488 |
| edge | 8 | 10.84 s | 0 / 8 | 7.959 | 0.115 | 3.434 |
| probe | 15 | 8.99 s | 1 / 15 | **8.088** | 0.067 | 3.493 |
| medium | 20 | 14.45 s | 18 / 20 | 7.981 | 0.073 | 3.452 |
| long | 8 | 14.59 s | 8 / 8 | 8.009 | 0.054 | 3.459 |
| **Full column** | 75 | 10.05 s | 27 / 75 | **8.002** | 0.097 | 3.453 |

All six strata score in the range **7.957–8.088** on AB.PQ —
truncation direction doesn't correlate with score. The **48 fully
complete files** (short + jargon + edge = 32, plus probe-14-of-15,
plus medium-2-of-20 = 48 complete of 75) score essentially the
same as the 27 truncated files. This means:

- **Orpheus's narration AB.PQ score of 8.00 is EARNED, not
  artifact.** The exclusion of Orpheus from the deployable-#2
  slot is a scope choice (don't rank truncated audio for narration
  workflows), not a statistical necessity. Speechify's SD_75 for
  narration PQ is 0.0943 (lowest of 8 vendors, the retained #1);
  Orpheus's is 0.0967 (2nd lowest); the substituted Cartesia's is
  0.1795. **The 9.5σ → 7.0σ shift under the Orpheus-exclusion is
  driven by Cartesia's higher SD inflating SE(diff), not by
  anything about Orpheus's variance.** And Orpheus's conversational
  AB.PQ SD is 0.2731 (2nd HIGHEST of 8, under identical 25/75
  truncation) — the "cap depresses variance" idea is directly
  falsified.
- **The −78.7 dBFS noise floor value** in the narration table
  is a **real Orpheus property**. Orpheus narration `speech_ratio`
  = **0.901** (from hygiene.json) — higher than Speechify's 0.875,
  and only slightly lower than ElevenLabs's 0.924. The clips are
  90% speech; the quiet noise floor is the Orpheus model's actual
  noise floor on the non-silence regions.
- **Speechify vs Orpheus (0.148, 9.5σ) is a real effect.** The
  paired-test recompute strengthens it further
  (`scripts/_paired_test.py`). Orpheus IS numerically #2 on
  AB.PQ narration.
- **The honest reason to demote Orpheus from the narration
  recommendation is Q1**, not the stats: the 14.59-s cap
  disqualifies it from long-form narration workflows regardless
  of the quality score. See the Q1 hard-constraint check in the
  Decision framework. The rankings table below shows both the
  Orpheus-included (numerical) and Orpheus-excluded (deployable)
  reads so the mechanism is transparent.

<a name="footnote-2-cartesia-narration-dnsmos"></a>
**Footnote ² (DNSMOS survivor-subset cells, all runs)**: DNSMOS
refuses to score files whose peak amplitude touches or exceeds
0 dBFS (`peak_out_of_range`); the refused cells drop out of the
per-vendor mean silently, so any cell where `n_valid < n_items`
is a **survivor-selected subset**, not the full column. Every
cell in the R2 tables above marked <sup>²</sup> is one such
subset, and there are more of them in R3:

| Run | Vendor | Use case | Valid / Items | Refused | Notes |
|---|---|---|---:|---:|---|
| R2 | cartesia | conversational | 43 / 75 | 32 (42.7%) | marked <sup>²</sup> on conv table above |
| R2 | cartesia | narration | 38 / 75 | 37 (49.3%) | marked <sup>²</sup> on narr table above |
| R2 | google | narration | 71 / 75 | 4 (5.3%) | marked <sup>²</sup> on narr table above |
| R3 | cartesia | conversational | 51 / 75 | 24 (32.0%) | (R3, not shown in R2 tables) |
| R3 | cartesia | narration | 37 / 75 | 38 (50.7%) | (R3, comparison-doc row |
| R3 | google | narration | 72 / 75 | 3 (4.0%) | (R3) |
| R3 | speechify | narration | 74 / 75 | 1 (1.3%) | (R3) |
| R3 | elevenlabs | conversational | 74 / 75 | 1 (1.3%) | (R3; also drives the n=74 in F-12's conv DNSMOS row) |

Whole-family framing: **Cartesia is the load-bearing case** —
its DNSMOS ranks on the surviving subset are still **#8 of 8**
on OVRL / SIG / BAK across both runs, so the mastering signature
that got the ~1/3 to ~1/2 of items refused persists in the ones
that made it through (F-4a). Google narr, Speechify narr, and
ElevenLabs conv R3 are all small refusal counts (1-4 items) but
should be read as `n_valid < 75` when comparing means.
Sources: `analysis/campaign-{20260809T204608Z,20260831T175358Z}/quality.json`
`dnsmos_by_provider[*].n_valid` per row.

<a name="footnote-3-deepgram-conversational-ttfa"></a>
**Footnote ³ (Deepgram conversational TTFA)**: the 583 ms figure
in this table is from a campaign-mode Deepgram row. The two
dedicated latency-mode sessions on 2026-08-09 (n=50 trials each,
serial) measured Deepgram at **p50 = 583 / 564 ms, p90 = 674 / 670
ms** — statistically consistent with the campaign value.
Deepgram wasn't re-measured in S2/S3, so we have two consistent
latency-mode sessions from the same day, not three days of data.

**Footnote † (Orpheus $/1K words)**: the $0.030 cell for Orpheus
in both the conversational and narration tables is a model output
under cost_model.py's default "100-word / 500-char session per
generation" assumption for per-generation vendors — see
[`src/veval/analyze/cost.py`](../src/veval/analyze/cost.py) line 177.
T8 measured Orpheus's actual per-call output as **14.59 s of audio
≈ 213 chars ≈ ~35 words per call**, not the assumed 500 chars /
100 words. Under the T8-measured per-call output, Orpheus's real
$/1K words is closer to **~$0.070-0.088** — see the honest
Orpheus split under [Cost calculus](#cost-calculus). The $0.030
number is retained in the table as the direct output of the v1
cost_model.json (auditability), not as a defensible per-word
figure. **Do not compare $0.030 across vendors as if it were a
peer of ElevenLabs' $0.22** — it is not derived on comparable
assumptions.

---

<a name="rankings-summary"></a>
## Rankings summary (R2 — `campaign-20260809T204608Z`)

**Top-2 per quality axis per use case** — the "who's actually
worth paying for?" table. Each pair is judged **significant** iff
`|Δ| > 1.96 × SE(diff)` where `SE(diff) = √(SE_a² + SE_b²)` and
`SE_i = SD(vendor's column) / √n_i`, with `n_i` = that cell's
`n_valid`. All published ranking rows below have n_i = 75 on the
Audiobox axes and n_i = 74-75 on the DNSMOS axes (three
DNSMOS-refused cells sit off the ranking rows shown here — see
[footnote ² below](#footnote-2-cartesia-narration-dnsmos)); the
formula is written per-cell so it stays correct as new
comparisons are added. Standard normal-approximation test at
α=0.05. Per-vendor per-signal SDs + SE_mean values are in
[`scripts/_noise_floor_recompute.py`](../scripts/_noise_floor_recompute.py)
output; run the script to reproduce.

**Why this method**:
- One number ("0.035 noise floor") applied across two different
  scales (Audiobox 0-10, DNSMOS 1-5) was scale-inconsistent
- The previous threshold was measured on Speechify — the winner
  whose margin it then adjudicated. This method pools across all
  8 vendors and computes SE per-comparison, no circularity
- Per-pair SE(diff) is the standard statistical rule, not a
  heuristic threshold

### Conversational

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | \|Δ\|/SE(diff) | Verdict |
|---|---|---:|---|---:|---:|---:|---|
| Audiobox PQ (cleanliness) | speechify | 7.897 | elevenlabs | 7.755 | +0.142 | **3.7σ** | **SIG_DIFF** |
| Audiobox CE (warm / enjoyment) | speechify | 6.462 | fish | 6.242 | +0.220 | **5.9σ** | **SIG_DIFF** |
| DNSMOS OVRL (clean) | openai | 3.489 | elevenlabs | 3.467 | +0.022 | 1.3σ | **TIE** |
| DNSMOS SIG (clean) | openai | 3.697 | elevenlabs | 3.686 | +0.011 | 0.8σ | **TIE** |

### Narration

**Numerical rankings** (all 8 vendors, Orpheus included — this is
the AS-MEASURED table):

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | \|Δ\|/SE(diff) | Verdict |
|---|---|---:|---|---:|---:|---:|---|
| Audiobox PQ (cleanliness) | speechify | 8.150 | orpheus¹ | 8.002 | +0.148 | **9.5σ** | **SIG_DIFF** |
| Audiobox CE (warm / enjoyment) | speechify | 6.662 | elevenlabs | 6.466 | +0.197 | **7.3σ** | **SIG_DIFF** |
| DNSMOS OVRL (clean) | openai | 3.463 | orpheus¹ | 3.453 | +0.010 | 0.7σ | **TIE** |
| DNSMOS SIG (clean) | openai | 3.679 | deepgram | 3.677 | +0.002 | 0.2σ | **TIE** |

**Deployable rankings** (Orpheus excluded because Q1's 14.59-s
output-cap gate disqualifies it from narration workflows,
regardless of its per-call quality — see [footnote ¹](#footnote-1)
for the per-stratum receipt showing Orpheus's aggregate is
earned, not artifact):

| Axis | #1 vendor | #1 score | Deployable #2 | #2 score | Δ | \|Δ\|/SE(diff) | Verdict |
|---|---|---:|---|---:|---:|---:|---|
| Audiobox PQ (cleanliness) | speechify | 8.150 | cartesia² | 7.986 | +0.164 | **7.0σ** | **SIG_DIFF** |
| Audiobox CE (warm / enjoyment) | speechify | 6.662 | elevenlabs | 6.466 | +0.197 | **7.3σ** | **SIG_DIFF** |
| DNSMOS OVRL (clean) | openai | 3.463 | deepgram² | 3.442 | +0.021 | 1.1σ | **TIE** |
| DNSMOS SIG (clean) | openai | 3.679 | deepgram | 3.677 | +0.002 | 0.2σ | **TIE** |

<a name="footnote-1"></a>
¹ **Orpheus AB.PQ narration 8.002 is EARNED, not a truncation
artifact.** Splitting the 75 narration items by whether Orpheus's
14.59-s output cap truncated them (`total_seconds > 14.5` in
`hygiene.json`): **48 complete items** produce AB.PQ mean 8.009;
**27 truncated items** (long 8/8, medium 18/20, probe 1/15) produce
mean 7.989 — Δ ≈ 0.02, both essentially at Orpheus's overall
narration mean of 8.002. The 9.5σ Speechify-vs-Orpheus lead is a
real per-call rendering-consistency effect, not a truncation-
collapsed-variance artefact. Same story for DNSMOS OVRL narration.
**The reason to demote Orpheus from the deployable ranking is Q1**
(14.59-s cap disqualifies real narration), not statistics. Prior
text-length grouping retracted; see
[CORRECTIONS row 19](../CORRECTIONS.md).

² Cartesia is the deployable AB.PQ #2 (Speechify vs Cartesia 7.0σ);
Deepgram is the deployable DNSMOS OVRL #2 on narration (OpenAI vs
Deepgram 1.1σ — OpenAI is #1 on DN.ovrl in both use cases). Under
the paired test the Orpheus tie call for DNSMOS OVRL tightens
slightly but stays a tie; the AB.PQ 9.5σ tightens further.

**Interpretation:** All four Audiobox comparisons are meaningfully
different in both the numerical and deployable rankings — Speechify's
lead over the (deployable) #2 vendor is **3.7σ to 7.3σ
significant**, or 3.7σ to 9.5σ if the Orpheus row is retained.
Note the Audiobox lead splits across two axes with different
construct behaviour (F-8): AB.PQ agrees with DNSMOS (cleanliness),
AB.CE anti-correlates with DNSMOS (warmth / enjoyment). So
Speechify's Audiobox win is a **cleanliness win on one axis and
a warmth win on the other**, not a monolithic "warm-rater" win.
All DNSMOS top-1-vs-top-2 comparisons are ties — OpenAI's DNSMOS
"win" is essentially indistinguishable from ElevenLabs (conv),
from Deepgram or Orpheus (narr).

### Paired vs unpaired: which test and why

Every vendor speaks **the same 75 corpus items**. A paired test
matches items across vendors and cancels item-level effects
(hard-to-say items score low for everyone; that noise is shared
and drops out of the paired Δ). The paired formula is
`SE_paired = SD(Δ_i) / √75` on the item-matched deltas; the
unpaired formula above assumes vendor-a and vendor-b are
independent samples and inflates SE.

The tables above use the **unpaired** formula. It is the
**more familiar** SE-of-the-means formula, but it is *not*
uniformly conservative — the direction of its bias depends on the
verdict:

- For **SIG_DIFF verdicts**: unpaired understates significance
  (paired σ ratio is always ≥ unpaired), so the reported σ is a
  **floor on significance**. Reading a headline "3.7σ" as "at
  least 3.7σ" is correct.
- For **TIE verdicts**: unpaired *inflates* SE(diff) → *lowers* the
  σ ratio → makes "tied" *easier* to declare. Unpaired is
  **anti-conservative** for tie calls. A tie under the unpaired
  test may or may not be a tie under the paired test — the paired
  test can promote it to borderline-significant (as it does for
  OpenAI vs ElevenLabs conv DNSMOS OVRL below).

We chose the unpaired formula for the headline because the
"SE-of-the-means" notation is more familiar and easier for a
reader to reproduce from a scalar mean + SD. **Both directions
of bias are made explicit** in the paired-vs-unpaired table
below — nobody has to trust an "unpaired is conservative" claim
that only holds for half the verdicts.

Recomputed with the paired test — [`scripts/_paired_test.py`](../scripts/_paired_test.py):

| Comparison | Unpaired | Paired | Paired/unpaired |
|---|---:|---:|---:|
| Speechify vs ElevenLabs · conv AB.PQ | 3.7σ | **6.0σ** | 1.63× |
| Speechify vs Fish · conv AB.CE | 5.9σ | **14.2σ** | 2.40× |
| Speechify vs Cartesia · narr AB.PQ | 7.0σ | **9.0σ** | 1.29× |
| Speechify vs ElevenLabs · narr AB.CE | 7.3σ | **17.2σ** | 2.36× |
| OpenAI vs ElevenLabs · conv DNSMOS OVRL | 1.3σ | **2.0σ** | 1.54× |
| OpenAI vs ElevenLabs · conv DNSMOS SIG | 0.8σ | 1.3σ | 1.66× |
| OpenAI vs Deepgram · narr DNSMOS OVRL | 1.1σ | 1.5σ | 1.41× |
| OpenAI vs Deepgram · narr DNSMOS SIG | 0.2σ | 0.2σ | — |

**What this changes**:
- All four Audiobox SIG_DIFF calls **strengthen** under the paired
  test. No SIG_DIFF verdict is at risk of flipping.
- Three of the four DNSMOS tie calls hold cleanly. **One (OpenAI vs
  ElevenLabs conv OVRL) moves from 1.3σ to 2.0σ — right at the
  α=0.05 boundary.** Under the paired test alone, this pair is
  borderline rather than "clearly tied." The unpaired-headline
  "TIE" call is a conservative reading; the paired test says
  "borderline" and a proper answer would need a multiplicity
  correction (see next section) before publishing "significantly
  different." We leave the tie verdict standing in the headline
  tables and flag the paired-test borderline here so readers can
  see the direction of the sensitivity.
- The 1.63×-2.40× paired/unpaired ratio means item-level effects
  are strong. This matches intuition: a warm reading of item S07
  will score high across all vendors; the item-level baseline is
  shared corpus content.

**Why unpaired stays in the headline** (recap): reproducibility
and familiarity, not conservatism. Unpaired is a *floor* on
significance for SIG_DIFF calls but an *inflated* SE for TIE
calls — the paired-test row for OpenAI vs ElevenLabs conv
DNSMOS OVRL (1.3σ → 2.0σ, tie → borderline) is the receipt for
the second direction. Readers who want the tighter test should
use the paired column above; both are published so the
sensitivity is visible.

### Statistical caveats (multiplicity, effect size, perceptual calibration)

Three things the σ ratios above do **not** answer:

**1. Multiplicity is uncorrected.** The rankings tables run 4
Audiobox + 4 DNSMOS = 8 top-1-vs-top-2 comparisons at α=0.05
without a family-wise or false-discovery correction. Under
Bonferroni for 8 comparisons the per-test α would drop to 0.00625
(≈ 2.73σ). All four Audiobox SIG_DIFF calls (3.7σ – 9.5σ unpaired,
i.e. 3.7σ – 7.3σ under the deployable-ranking substitution;
6.0σ – 17.2σ paired) clear that bar comfortably. All four DNSMOS
tie calls are unaffected (they were below 1.96σ already). **The
one comparison sensitive to multiplicity is OpenAI vs ElevenLabs
conv DNSMOS OVRL**, which sits at 2.0σ paired and would flip from
"borderline significant" back to "tie" under Bonferroni. Reported
here rather than picked-and-published. A proper Tukey HSD on the
full 8-vendor pairwise matrix per axis would tighten this further
and is a v2 workstream.

**2. σ measures precision of the estimate, not perceptual
magnitude.** A 17.2σ paired result on narration Audiobox CE means
"the 0.20 gap between Speechify and ElevenLabs is measured with
enough precision to be certain it's not zero," **not** "the gap
is large." The absolute Δ is 0.20 on a 0–10 scale = **2% of the
scale**. Whether a 2% Audiobox delta is perceptible to a human
listener depends on the mapping from Audiobox score to
listener-preference — which is what the deferred multi-rater BT
panel (D-H) exists to establish. Until that pass exists, σ ratios
tell you the *direction* is real and the *estimate* is precise;
they do not tell you the *audible size* of the gap.

**3. There is no perceptual calibration.** The n=1 self-rating
review (D-H) did not run a multi-rater BT panel. We cannot map an
Audiobox Δ of 0.14 or 0.20 to "X% of listeners would pick vendor
A over B in a blinded pair." A future v2 pass would run the
`veval rate {build,normalize,serve,fit}` pipeline (implemented in
[`src/veval/human/`](../src/veval/human/) — `pair_builder.py`,
`loudness.py`, `bt.py`) with 15–30 blinded raters and compare BT
rankings to the two machine-pipeline rankings — see
[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md#1-no-human-perceptual-validation-n1-rater-is-not-enough).

**What we CAN claim** from the current statistics: the four
Audiobox SIG_DIFF calls are robust (survive both the honest-#2
substitution for narration PQ and Bonferroni correction). The
four DNSMOS ties are robust (three cleanly, one at the boundary).
**What we CANNOT claim**: that the observed score deltas are
audible to a human listener, or that the SIG_DIFF verdicts
translate to preference-share in a blinded A/B.

---

## Cross-pipeline agreement (F-8)

Two independent MOS pipelines rank the 8 vendors **differently**.
Cross-pipeline mean Spearman ρ across the 8 vendors:

| Use case | Cross-pipeline mean ρ | Point-estimate reading | 95% CI (Fisher-transformed, n=8) |
|---|---:|---|---|
| Conversational | **−0.13** | Essentially uncorrelated | roughly [−0.75, +0.60] |
| Narration | **−0.27** | Weakly inverse | roughly [−0.81, +0.51] |

**Statistical caveat**:
n=8 vendors gives Spearman ρ a very wide 95% CI. We **cannot claim**
either point estimate is significantly different from zero, nor from
a strong positive correlation. What we can claim is that the two
pipelines do NOT show the strong positive rank correlation we
would expect if they measured the same construct — and we have
specific per-vendor rank inversions (OpenAI narration Audiobox #8
vs DNSMOS three-scale #1/#1/#2; Cartesia narration Audiobox #3 vs
DNSMOS surviving-subset #8/#8/#8) that are directly citable.

See [documentation/figures/f1_rank_inversion.png](figures/f1_rank_inversion.png)
for the vendor-by-vendor rank comparison, and
[06_KEY_FINDINGS.md § F-8](06_KEY_FINDINGS.md#f-8) for the full
finding writeup + interpretation.

---

## Phase 2 additions

Two follow-up questions from Phase 1 got answered by the Phase 2
experiment pack (2026-09-01, ~$3.55 total metered). Full writeup
in [EXPERIMENTS_2026-09-01.md](EXPERIMENTS_2026-09-01.md); the
two tables that directly extend the primary results above:

### Cross-vendor loudness-fade rate on long-form narration

Every vendor's pinned narration voice, R3 primary-campaign
L01..L08 audio, run through the drift analyzer (fade =
Δ(t1−t3) ≥ 2 dB AND monotonically decreasing across thirds):

| vendor | fade rate | mono-decr any magnitude | fading items |
|---|---:|---:|---|
| **ElevenLabs** | **2 / 8 (25%)** | 4 / 8 | L02 (+2.59 dB), L06 (+2.86 dB) |
| Deepgram | 1 / 8 (12%) | 2 / 8 | L01 (+2.49 dB) |
| Orpheus | 1 / 8 (12%) | 2 / 8 | L02 (+2.18 dB) |
| Cartesia, Fish, Google, OpenAI, Speechify | 0 / 8 (0%) | 0-3 / 8 | – |
| **Cross-vendor** | **4 / 64 (6.2%)** | **15 / 64 (23.4%)** | see per-vendor above |

**Companion finding — the fade is stochastic across runs of the
same voice**: ElevenLabs L03 does NOT fade on charlotte in the
R3 campaign audio (Δ = −0.26 dB, non-monotonic) — but fades
2.79 dB on the same voice, same text, generated same-day in
Phase 2's Experiment B. F-6 refined from "reproducible L03
quirk" to "run-level stochastic fade at ~5-25% rate on affected
voices; chunking to ≤500 chars mitigates." See
[06 § F-6](06_KEY_FINDINGS.md#f-6--monotonic-loudness-fade-on-long-form-tts-narration--a-cross-vendor-phenomenon-at-5-25-base-rate)
and Phase 2's [Follow-up 1](EXPERIMENTS_2026-09-01.md#follow-up-1--cross-vendor-pinned-voice-fade-rate-on-the-primary-campaign).

### Alt-voice AB.PQ shift on same 8 long items (paired-t, 4 vendors)

Same L01..L08 narration, pinned voice from R3 vs one alt voice
from the same vendor's library (Phase 2 Experiment E). Reported
as the **paired difference on AB.PQ** — the project's standard
inferential test, matched pairs on the same 8 items, p reported
at **df = 7**:

| vendor | pinned R3 mean | alt E mean | mean Δ (alt − pinned) | SD_diff | SE_diff | **paired t (df 7)** | p (two-sided) |
|---|---:|---:|---:|---:|---:|---:|---:|
| OpenAI | 7.619 | 7.473 | **−0.146** | 0.126 | 0.044 | **−3.28** | 0.0135 |
| Fish | 7.710 | 7.869 | **+0.159** | 0.089 | 0.031 | **+5.06** | 0.0015 |
| Google | 8.032 | 7.927 | **−0.105** | 0.040 | 0.014 | **−7.35** | 1.6×10⁻⁴ |
| Deepgram | 7.948 | 7.468 | **−0.480** | 0.101 | 0.036 | **−13.46** | 2.9×10⁻⁶ |

**All four alt voices produce a statistically significant AB.PQ
shift from the pinned voice on the same 8 items** (|t| ≥ 3.28 in
every case at df=7, all p < 0.05; the smallest, OpenAI, is
p = 0.0135). Direction varies (Fish +, others −); magnitude
varies substantially (OpenAI −0.146 to Deepgram −0.480). Test
statistics themselves (t values) are exact and unchanged; p
column normal-approximation tails retracted; see
[CORRECTIONS row 172](../CORRECTIONS.md). Matching change in
[EXPERIMENTS Follow-up 4](EXPERIMENTS_2026-09-01.md#paired-t-per-vendor-the-projects-standard-inferential-test).

**Gender confound**: all four alt voices tested here crossed
gender against the pinned voice — OpenAI onyx (male) → nova
(female), Deepgram orion (male) → luna (female), Google Charon
(male) → Kore (female). Fish uses opaque UUIDs so the pinned/alt
gender pair is not directly verifiable from configs, but the
pinned was narration-tagged and the alt was Fish's
conversational-tagged voice — a *different* design confound
(voice-purpose swap).

**Google DNSMOS attrition on this same 8-item set**: the AB.PQ
paired test above runs on n=8 for every vendor (Audiobox accepted
all 16 Google files on both sides). On the DN.ovrl axis, however,
DNSMOS refused **3 of 8 Google pinned files** (L02, L03, L04, all
peak-out-of-range from clipping — same defect that gates Google
on `long_stratum_clipped_samples`) and 1 of 8 Google alt files
(L02, same cause), leaving 5 items valid on both sides. The
DN.ovrl comparison for Google is therefore reported in
[Follow-up 4's comparison table](EXPERIMENTS_2026-09-01.md#the-comparison-table-alt-voice-vs-pinned-voice-l01l08)
as an intersection paired delta on those 5 items (Δ +0.079,
paired t = +3.16 at df=4 for n=5, p = 0.034 two-sided — borderline at α=0.05), footnoted parallel to the Cartesia survivor-subset
pattern elsewhere in this doc. AB.PQ / AB.CE / WER on Google are
unaffected (all n=8). **T6's Speechify comparison split by use
case**: conversational `geffen_32` (female) → `edmund_32` (male)
crossed gender, but **narration `wyatt_32` (male) → `edmund_32`
(male) was same-gender** (verified in
[T6 verdict](../analysis/verification/T6_speechify_voice_bias.md), which says of the narration pair "same gender (both male)").
Recomputed paired-z on the T6 20-item set (matched on item_id):
**narration same-gender swap = +0.103 AB.PQ (+4.02σ)**;
conversational cross-gender swap = +0.299 (+6.05σ). **T6
narration already shows a >3σ voice-choice effect that survives
gender matching**, so the four Follow-up-4 cross-gender pairs are
not the only same-vendor voice-choice signal — voice choice
matters at ≥3σ even within one gender within one vendor. What
Phase 2's 4-vendor sweep does add is that the magnitude ranges
3× across vendors (OpenAI 0.146 to Deepgram 0.480 on AB.PQ,
under a cross-gender confound); a same-gender sweep across the
other vendors is still v2 workstream (see
[07 § gap 2](07_GAPS_AND_FUTURE_WORK.md#2-one-voice-per-vendor-per-use-case-partially-closed-by-phase-2)).

**What the data actually supports**: voice choice matters
materially within every vendor tested, at every measured axis;
the magnitude of the shift ranges over 3× (OpenAI 0.146 to
Deepgram 0.480 on AB.PQ); the sign is not stable across vendors;
and voice choice within a vendor shifts AB.PQ at ≥3σ even under
same-gender swap on Speechify (T6 narration). **Speechify's T6
result — that its alt voice ranked #1 on AB.PQ with a +0.30 (conv)
/ +0.10 (narr) numerical lead over the
pinned voice — remains a rank-preservation observation, not a
"holds within noise" claim.**

See
[06 § F-7](06_KEY_FINDINGS.md#f-7)
and Phase 2's [Follow-up 4](EXPERIMENTS_2026-09-01.md#follow-up-4--alt-voice-qualitywer-analysis-on-experiment-e-audio).

---

## Cost calculus

Cost per 1K words at the 100K-words/month tier, from
[configs/pricing.yaml](../configs/pricing.yaml). Full pricing model
in [`analysis/campaign-*/cost_model.json`](../analysis) — includes
monthly minimums, included tiers, and rates at 10K/100K/1M words
per month tiers.

**Shared assumption for the whole table**: `cost_model.py`
converts char-billed vendors' rates to $/1K words using
`chars_per_word_assumption = 5.0` (declared in
[`cost_model.json`](../analysis/campaign-20260809T204608Z/cost_model.json)).
The actual corpus averages **5.77 chars/word** (5.67 conv, 5.87
narr) as measured across all 150 corpus items (75 conv + 75 narr;
6,741 words, 38,916 chars). That means **every char-billed vendor's $/1K words in
the table is under-stated by roughly (5.77 − 5.00) / 5.00 = 15%**
against the actual corpus. Char-billed vendors in this table are
OpenAI (per_1M_chars), Fish, Speechify, Deepgram, Google,
Cartesia, ElevenLabs (all per_1M_chars or per_1M_bytes). Orpheus
is per_generation and has its own footnote †.

**The ratios that drive the recommendations survive this scale
factor** — Speechify is still 45% of ElevenLabs at 100K/mo, OpenAI
is still 34% of ElevenLabs and 50% of Deepgram, etc. — because a
common multiplicative correction cancels out of a ratio. **The
absolute prices in the table are v1's `cost_model.json` output
under 5.0 chars/word.** A future v2 pass will re-run the model at
5.77 chars/word (or, more honestly, use the actual observed corpus
chars per row rather than an assumption); the recomputation is
`observed_cost / observed_words` per row and does not require
re-generating audio.

| Vendor | $/1K @ 10K/mo | $/1K @ 100K/mo | $/1K @ 1M/mo | Notes |
|---|---:|---:|---:|---|
| orpheus | 0.030 † | 0.030 † | 0.030 † | See ⚠ below — per-generation vendor; the $0.030 is `cost_model.py`'s output under a stale default that predates T8's per-call output-cap measurement. |
| **openai** | 0.075 | **0.075** | **0.075** | tts-1-hd (narration) + gpt-4o-mini-tts (conv). Char-billed → scale up ~15% for corpus-actual 5.77 chars/word. |
| fish | 0.075 | 0.075 | 0.075 | s2.1-pro (paid); split-model design (quality vs latency). Char-billed. |
| **speechify** | **1.000** ⚠ | **0.100** | **0.040** | Starter $10/mo covers 100K; at 10K/mo you're paying the $10 subscription for 10K words = $1.00/1K, so at 10K/mo Speechify is the 2nd-most-expensive vendor (only ElevenLabs Creator's $2.20 is worse). Char-billed. Value from `cost_model.json` `speechify.dollars_per_1k_words_at.10K_words_per_month`. |
| deepgram | 0.150 | 0.150 | 0.150 | Aura-2; $200 signup credit covers early volume. Char-billed. |
| google | 0.150 | 0.150 | 0.150 | Chirp3-HD. Char-billed. |
| cartesia | 0.500 | 0.160 | 0.196 | Pro $5/mo = 100K credits, then per-1M rate. Char-billed. |
| **elevenlabs** | **2.200** | **0.220** | 0.244 | Creator $22/mo = 121K credits; expensive at low volume. Char-billed. |

**⚠ Orpheus $/1K-words is a model artefact, not a comparable price**

The table row for Orpheus reports **$0.030/1K words** at every
tier. **This number is `cost_model.py`'s output under a default
assumption that predates T8's per-call output-cap measurement.**
Reproduced from the actual code path in
[`src/veval/analyze/cost.py`](../src/veval/analyze/cost.py) line 177:
for per-generation vendors the model uses `avg_chars = CHARS_PER_WORD × 100 = 500 chars per call` (a "100-word default session" assumption).
So at 100K words/month:
- projected calls per month = 100,000 × 5.0 / 500 = **1,000 calls**
- cost = 1,000 × $0.003 = **$3.00** = $0.030/1K words

**T8 established the real per-call output**: exactly **14.59 s of
audio ≈ 213 chars ≈ ~35 words per call** (invariant across every
long item; stdev = 0.00 s). Under T8's measurement the real math
at 100K words/month is:
- calls per month = 100,000 words / ~35 words per call = **~2,850 calls**
- cost = 2,850 × $0.003 = **~$8.55/mo = ~$0.086/1K words**

Or equivalently in chars: 5 calls per 1K chars × $0.003 = $0.015/1K
chars = **~$0.088/1K words** at 5.87 chars/word (narration corpus).

Both derivations land in the **~$0.067-0.088/1K words** band, not
$0.030. On the observed corpus (150 items, 6,741 words) the
pipeline used one call per item and produced 150 calls × $0.003 =
$0.45, so the as-generated per-word cost is $0.45 / 6.741K words
= **$0.067/1K words** — close to the T8-based rendered-audio
estimate above.

**Two honest Orpheus prices to think about:**

- **Conversational (short turns that fit in one 14.59-s call)**:
  ~$0.003 per call × turns-per-1K-words. Cheap per turn, but at
  ~35-46 words per turn that's ~25 calls / 1K words = **~$0.07-0.09
  / 1K words** — the same order of magnitude as OpenAI ($0.075).
- **Narration (must chunk long items to complete)**: ~5 calls /
  1K chars = **~$0.088 / 1K words**. Still similar order of
  magnitude to OpenAI, not the category-crushing $0.030 the
  table suggests.

**The $0.030 row is retained** as the direct output of the v1
cost_model.json (auditability). **Do not compare $0.030 against
ElevenLabs' $0.22 as if they were peer prices** — they are not
derived on comparable assumptions. Orpheus is out on Q1 for real
narration because of the 14.59-s output cap anyway (see § Decision
framework).

**Three cost-driven conclusions** (updated after the noise-floor
recompute confirmed the tie calls at 0.2-1.3σ; see Rankings summary
above):

1. **DNSMOS conversational is a tie between OpenAI and ElevenLabs**
   (Δ = +0.022, 1.3σ). OpenAI at **$0.075** vs ElevenLabs at
   **$0.22** — OpenAI is **34% of ElevenLabs' price** (i.e. **66%
   saving**) at 100K wpm/mo tier. Same story at 1M/mo tier (OpenAI
   $0.075 vs ElevenLabs $0.244, 31% of ElevenLabs' price, ~69% saving).
2. **DNSMOS narration is a tie between OpenAI and Deepgram**
   (Δ = +0.021, 1.1σ). OpenAI at $0.075 is **50% of Deepgram's
   $0.15** — ~50% saving. Same at 1M/mo. (Orpheus also tied on this
   axis but disqualified for narration — see rankings footnote 1.)
3. **Speechify wins Audiobox AND is cheap** on both use cases —
   $0.10/1K at 100K/mo, $0.04/1K at 1M/mo. Unusual combination
   (quality winner is usually the priciest).

See [documentation/figures/f2_cost_vs_quality.png](figures/f2_cost_vs_quality.png)
for the visual.

---

## Latency (up to 6 sessions across 4 dates, with concurrent ping baseline on S3)

Time-to-first-audio-frame (TTFA), 50 serial trials per session,
conversational S01 corpus item. **Six latency-mode runs total for
the speed-critical vendors** across 2026-08-09 (S1a, S1b same day),
2026-08-11 (S2), 2026-08-12 (S3, with concurrent ping baseline),
and 2026-09-01 (S4, S5 same day — added by Phase 2's
[Follow-up 3](EXPERIMENTS_2026-09-01.md#follow-up-3--d-latency-sanity-check)).

| Vendor | S1a p50/p90 | S1b p50/p90 | S2 p50/p90 | S3 p50/p90 | **S4 p50/p90** | **S5 p50/p90** | Sessions | Range summary |
|---|---|---|---|---|---|---|---|---|
| **elevenlabs** (Flash v2.5) | 439 / 479 | 440 / 474 | **424 / 469 (n=40)** ¹ | **694 / 816 (n=40)** ¹ | **412 / 461** | **421 / 468** | 6 | p50: 412–694 ms (+68% max) |
| openai (gpt-4o-mini-tts) | 736 / 956 | 762 / 946 | 936 / 1493 | **1369 / 1882** | **772 / 1212** | **783 / 1206** | 6 | p50: 736–1369 ms (+86% max) |
| deepgram | 583 / 674 | 564 / 670 | not re-measured | not re-measured | not re-measured | not re-measured | 2 same-day | p50: 564–583 ms (no cross-day range measured) |
| cartesia | 467 / 529 | 468 / 530 | not re-measured | not re-measured | not re-measured | not re-measured | 2 same-day | p50: 467–468 ms (no cross-day range measured) |
| speechify · fish · google · orpheus | not applicable* | | | | | | 0 | adapters don't stream |

¹ ElevenLabs S2 and S3 both landed **n=40** trials (not 50);
verified against `analysis/latency-20260811T183202Z/latency.json`
and `analysis/latency-20260812T191323Z/latency.json` `n_items = 40`.
S1a and S1b (both 2026-08-09) landed full n=50. The mechanism that
truncated S2/S3 (subscription credit exhaustion, spend cap, or
per-session request cap) is not diagnosed; the fact that both
later sessions stopped at 40 is documented as measured.

**Every measured streaming vendor's p90 exceeds the pre-registered
400 ms `ttfa_p90_ms` gate** in every session in which they were
measured. ElevenLabs at **461 ms (S4)** is the closest to the
threshold across all 6 sessions (S1a 479, S1b 474, S2 469, S3 816,
S4 461, S5 468) but still failed. See the
[Pre-registered gate outcomes § TTFA-gate admission](#ttfa-gate-admission)
section below for the full pass/fail table.

*"Not applicable" here means the adapter doesn't stream (Speechify
JSON envelope per D-008; Fish's paid model split; Google's
non-streaming; Orpheus's hosted-inference-poll pattern on Replicate).
TTFA is `total_ms` for these, not the streaming TTFA the other
providers report. See [../DEVIATIONS.md](../DEVIATIONS.md#d-008).

**Concurrent ping baseline during S3** (Cloudflare 1.1.1.1,
274 probes, 500 ms interval): p50 = 8 ms, p90 = 12 ms, min = 5 ms,
max = **29 ms**, stdev = 3.2 ms, 0 errors. **The last-mile link
to Cloudflare 1.1.1.1 was clean during S3.** This rules out only
the "ISP dropped packets during the window" hypothesis; it does
NOT rule out DNS-resolution jitter to vendor endpoints, TLS-handshake
variance, client-side event-loop stalls, or vendor-side capacity
(none of which share ICMP's code path). See F-11 for the full
scope-of-ruleout list.

**Table caveat**: ElevenLabs S2 and S3 both landed n=40 (not 50)
— see the ¹ footnote under the table above and F-11 for the
mechanism-not-diagnosed disclosure. n=40 still gives a
well-defined p50/p90 at this magnitude (SE of p90 ≈ 40 ms, small
vs. the +58% S1→S3 shift); anything past p90 for S2/S3 is
under-sampled.

**Portable findings** (across all 6 sessions):

- **Vendor ranking on TTFA is stable**: ElevenLabs is consistently
  faster than OpenAI in every one of the 6 sessions (p50 range
  ElevenLabs 412–694 vs OpenAI 736–1,369). The ordering is
  portable at n=6.
- **Absolute TTFA is NOT stable** for either vendor. Descriptive
  ranges excluding S3: **ElevenLabs p50 412–440 ms (6.8%), p90
  461–479 ms (3.9%); OpenAI p50 736–936 ms (27%), p90 946–1,493
  ms (58%)**. ElevenLabs is descriptively tighter; both fail the
  "quotable as a vendor spec" bar.
- **The observed variability is not our last-mile link** during
  S3. Beyond that, "wide-tail vendor" vs "client-side
  contamination" attribution is not separable at n=6 without the
  client-side event-loop lag logging Phase 1 called for as a
  control — that logging was not run on any of the 6 sessions.
- **Six sessions cleared the ≥5-session count Phase 1 called out**
  for characterising per-vendor variance, but the mechanism
  attribution workstream remains v2. Rank claims survive at n=6;
  stability *attribution* still needs ≥5-10 sessions across ≥2
  weeks *with* per-trial client-lag logging.

See [documentation/figures/f3_latency_stability.png](figures/f3_latency_stability.png)
for the latency-stability visual with concurrent ping-baseline annotation.
Full write-up in
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11).
Verdict details in
[analysis/verification/T5](../analysis/verification/T5_openai_latency.md)
and [T7](../analysis/verification/T7_elevenlabs_ttfa.md).

### <a name="rtf-admission"></a>RTF (real-time factor) — adjudicated on R3: 5 pass / 3 fail

**RTF was pre-committed as the narration latency gate**
(`rtf ≥ 3.0`; see [`configs/gates.yaml`](../configs/gates.yaml))
and is intended to fire on **long-narration throughput**. RTF is
defined as `decoded_audio_seconds / total_wall_clock_seconds`
(higher is faster).

**R3 campaign adjudication**: `campaign-20260831T175358Z` ran with
`--no-cache` — `n_fresh = 75` and `n_with_total = 75` for every
(vendor, use case) pair (Orpheus conv is 74 / 74; one call failed
silently — see [CORRECTIONS row 30](../CORRECTIONS.md)) in
[`analysis/campaign-20260831T175358Z/latency.json`](../analysis/campaign-20260831T175358Z/latency.json).
Every narration long-stratum item therefore has fresh
`synthesis_time`, populating `long_stratum_rtf_p50` for all
8 vendors (`long_stratum_n = 8` each):

| Vendor | long_stratum_rtf_p50 | Gate (`rtf ≥ 3.0`) |
|---|---:|---|
| OpenAI | **10.37** | ✓ PASS |
| ElevenLabs | **6.79** | ✓ PASS |
| Speechify | **6.58** | ✓ PASS |
| Google | **6.03** | ✓ PASS |
| Cartesia | **3.70** | ✓ PASS |
| Deepgram | 2.14 | ✗ FAIL |
| Fish | 1.70 | ✗ FAIL |
| Orpheus | 0.83 | ✗ FAIL (slower than real-time) ⚠ |

**Result: 5 pass / 3 fail.** This is the **first pre-registered
gate in the evaluation with a discriminating outcome** — the WER
gate failed all 8, the TTFA gate failed all 4 measured, the
conversational clipping gate isolated Cartesia + one other vendor
per run (Speechify 1 sample R2, ElevenLabs 1 sample R3). RTF actually
splits the roster.

**Is the 3.0 threshold arbitrary?** This is what the pre-registered
gate-robustness sweep is for.
[`configs/gates.yaml`](../configs/gates.yaml) carries
`robustness_points: [2.0, 3.0, 5.0, 10.0]` for this gate;
`veval score` runs the sweep and writes it to
[`analysis/campaign-20260831T175358Z/score.json`](../analysis/campaign-20260831T175358Z/score.json).
Marginal per-gate survivors on `long_stratum_rtf_p50`:

| threshold | marginal survivors | vendors |
|---:|---:|---|
| ≥ 2.0 | 6 | Cartesia, Deepgram, ElevenLabs, Google, OpenAI, Speechify |
| **≥ 3.0 (pre-registered)** | **5** | Cartesia, ElevenLabs, Google, OpenAI, Speechify |
| ≥ 5.0 | 4 | ElevenLabs, Google, OpenAI, Speechify |
| ≥ 10.0 | 1 | OpenAI |

The 5-vendor survivor set at the pre-registered 3.0 threshold is
stable to a small threshold change (dropping to 4 at 5.0), but
collapses to one vendor (OpenAI alone) at 10×. The published
5-of-8 discrimination isn't an artefact of picking exactly 3.0;
it is stable inside the 2-5 band and only becomes single-vendor
at the aggressive 10.0 endpoint.

**Orpheus caveat**: `long_stratum_rtf_p50 = 0.83` measures
wall-clock against the **truncated 14.59-s output** (see F-5 and
[T8](../analysis/verification/T8_orpheus_cost.md)), not against
the full requested content. Even under that generous denominator,
Orpheus is slower than real-time on this endpoint — the 3.0-gate
fail is unambiguous. A denominator based on requested content
would make the fail larger, not smaller.

**Historical S01-only data** (pre-R3 latency-mode sessions,
retained as measurement provenance): every session ran the
conversational S01 item (~2.6 s of audio), and no vendor cleared
3.0 on that workload — ElevenLabs S1b p90 (3.13) was the only
value above 3.0 in the whole S01 dataset, and every p50 was
well below 3.0. On S01, RTF is dominated by per-request overhead
and does not characterise sustained throughput; the R3
long-stratum table above is what the pre-registered gate targets.

| Session | Vendor | n | rtf p10 | rtf p50 | rtf p90 |
|---|---|---:|---:|---:|---:|
| S1b 2026-08-09 22:23 | deepgram | 50 | 0.84 | 0.91 | 1.02 |
| S1b 2026-08-09 22:23 | cartesia | 50 | 1.25 | 1.49 | 1.70 |
| S1b 2026-08-09 22:23 | elevenlabs | 50 | 2.66 | 2.90 | 3.13 |
| S1b 2026-08-09 22:23 | openai | 50 | 1.99 | 2.62 | 3.19 |
| S2 2026-08-11 | openai | 50 | 1.26 | 1.72 | 2.52 |
| S2 2026-08-11 | elevenlabs | 40 | 2.59 | 2.77 | 2.89 |
| S3 2026-08-12 | openai | 50 | 1.03 | 1.57 | 1.99 |
| S3 2026-08-12 | elevenlabs | 40 | 1.43 | 1.67 | 1.81 |

Prior "not adjudicated in v1" wording retracted; see
[CORRECTIONS row 24](../CORRECTIONS.md).

---

## <a name="pre-registered-gate-outcomes"></a>Pre-registered gate outcomes

**Which pre-committed gates did each vendor pass or fail?** The
gates were frozen in [`configs/gates.yaml`](../configs/gates.yaml)
under `prereg-v1` before any results existed (git-tagged). Applying
them strictly, on the campaign data:

### Conversational gates (4 gates in `configs/gates.yaml`; each row states its own denominator)

Sourced directly from
[`configs/gates.yaml`](../configs/gates.yaml)'s
`use_cases[0].gates` (conversational): four gates, no more.
The Fish conversational noise-floor observation is real (see N2)
but it was not gated by a pre-committed conversational rule — the
acoustic-noise-floor gate exists only under narration, as
`long_stratum_acoustic_noise_floor_dbfs`, applied to the 8
long-stratum items.

| Gate | Threshold | Pass | Fail | Exempt / N/A | Fail admission |
|---|---|---:|---:|---:|---|
| `ttfa_p90_ms < 400` | streaming, 4 measured | **0** | **4** | 4 (na_policy = exempt-and-annotate) | **Every measured streaming vendor fails.** Best measurement across all 6 sessions: ElevenLabs S4 at **461 ms** (S1a 479, S1b 474, S2 469, S3 816, S4 461, S5 468). All others (Cartesia 529, Deepgram 670-674, OpenAI 946-1882) fail more clearly. See [TTFA-gate admission](#ttfa-gate-admission) below. |
| `failure_incidence_pct < 2.0` (WER-based) | all 8 | R2: **0** / R3: **0** | R2: **8** / R3: **8** | 0 | **Every vendor fails in both rounds.** R2 failure incidence 61.3% (Fish, Speechify) to 73.3% (Orpheus). R3 64.0% (Fish, the R3 floor) to 78.4% (Orpheus). See [WER-gate admission](#wer-gate-admission) below. |
| `clipped_samples == 0` | all 8, conversational | R2: **6** / R3: **6** | R2: **2** / R3: **2** | 0 | **R2 fails**: Cartesia (406 total clipped samples across 54 files, ~5.4/item; F-4), Speechify (1 sample across 1 file). **R3 fails**: Cartesia (377 total), ElevenLabs (1 sample). Prior "7 pass / 1 fail | Cartesia only" wording retracted; see [CORRECTIONS row 52](../CORRECTIONS.md). |
| `commercial_use_permitted == 1` | all 8 | 8 | 0 | 0 | **Adjudicated against [`configs/capabilities.yaml`](../configs/capabilities.yaml) `commercial_use` column** (per-vendor `value` + `source_url` + `date_verified`, spec § A.8 D8 matrix). All 8 vendors on paid tiers permit commercial use; 6 as `yes` (paid public tier standard terms), Fish + Orpheus as `partial` (Fish free tier had commercial restrictions during the pre-2026-08-31 window; Orpheus community-fork's model licence should be re-read per-deployment). Row previously read "asserted, not evidenced" — closed by capabilities.yaml this round (see [CORRECTIONS row 162](../CORRECTIONS.md)). |

### Narration gates (4 gates; each row states its own denominator)

| Gate | Threshold | Pass | Fail | Exempt / not adjudicated | Fail admission |
|---|---|---:|---:|---:|---|
| `rtf ≥ 3.0` | narration long stratum, n=8 per vendor | **5** | **3** | 0 | **Adjudicated on R3** (`campaign-20260831T175358Z`, `n_fresh=75`, `n_with_total=75` per vendor per use case — Orpheus conv is 74/74, one call failed silently, see [CORRECTIONS row 30](../CORRECTIONS.md); `long_stratum_rtf_p50` for all 16 cells). Pass: OpenAI (10.37), ElevenLabs (6.79), Speechify (6.58), Google (6.03), Cartesia (3.70). Fail: Deepgram (2.14), Fish (1.70), Orpheus (0.83, slower than real-time; measured against the truncated 14.59-s output — see F-5). Full breakdown in [RTF admission](#rtf-admission) below. First pre-registered gate in the evaluation with a discriminating outcome (WER failed all 8; TTFA failed all 4 measured). |
| `monotonic_quality_drift_flag == 0` | TTSDS2-based | 0 | 0 | **8 (n/a — TTSDS2 skipped per D-A)** | see [D-B decision block](06_KEY_FINDINGS.md#d-b) |
| `long_stratum_acoustic_noise_floor_dbfs ≤ −40` | hygiene, long items only, worst-of-8 | R2: **6** / R3: **5** | R2: **2** / R3: **3** | 0 | **R2 fails**: Cartesia (worst = −37.47), ElevenLabs (worst = −37.93). **R3 adds Orpheus** as a third fail (worst-of-8 shifted from −52.78 in R2 to −27.75 in R3, +25 dB, most likely a truncation-tail artefact on the 14.59-s output cap). Full per-vendor R2/R3 table in [`round3-vs-round2-comparison.md § Hygiene`](../analysis/round3-vs-round2-comparison.md#hygiene-noise-floor-replication-variance-is-3-db-at-the-mean-level). Google is within ~2 dB of the gate on both runs and should be read as pass-with-uncertainty, not clean pass. Prior "Fish (persistent noise floor)" wording retracted; see [CORRECTIONS rows 31 + 32](../CORRECTIONS.md). |
| `long_stratum_clipped_samples == 0` | hygiene, long items only (L01–L08), worst-of-8 | R2: **5** / R3: **5** | R2: **3** / R3: **3** | 0 | **R2 fails**: Cartesia (224 clipped samples across all 8 long items), Google (36 across 4 long items), Speechify (3 across 1 long item). **R3 fails**: Cartesia (201 across 8), Google (28 across 3), Speechify (10 across 1). Prior "7 pass / 1 fail | Cartesia only" wording retracted; see [CORRECTIONS row 52](../CORRECTIONS.md). |

### <a name="ttfa-gate-admission"></a>TTFA-gate admission: every measured streaming vendor fails at 400 ms p90

The `ttfa_p90_ms < 400` conversational gate is applied against
the pre-registered threshold in
[`configs/gates.yaml`](../configs/gates.yaml). The rationale
committed with the gate is: "Perception degrades above ~500-600 ms
(spec A.1); 400 ms is a deliberate headroom margin below that,
since TTS latency is only one term in an agent's end-to-end
budget (LLM + TTS + network)."

Measured p90 by vendor and session (best measurement in bold):

| Vendor | S1a / S1b p90 | S2 p90 | S3 p90 | S4 p90 | S5 p90 | Best | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| ElevenLabs Flash v2.5 | 479 / 474 | 469 | 816 | 461 | 468 | **461 ms** (S4) | **FAIL** — closest to threshold |
| Cartesia | 529 / 530 | (not re-measured) | — | — | — | **529 ms** (S1a) | **FAIL** |
| Deepgram Aura-2 | 674 / 670 | (not re-measured) | — | — | — | **670 ms** (S1b) | **FAIL** |
| OpenAI gpt-4o-mini-tts | 956 / 946 | 1,493 | 1,882 | 1,212 | 1,206 | **946 ms** (S1b) | **FAIL** |
| Speechify · Fish · Google · Orpheus | not applicable — adapters don't stream | | | | | | exempt (na_policy = exempt-and-annotate, see D-008) |

**Every measured streaming vendor fails the pre-registered gate.**
The gate as committed is non-discriminating on this data.

**Where does the gate start to discriminate?** This is exactly
what the pre-registered gate-robustness sweep in
[`configs/gates.yaml`](../configs/gates.yaml)'s
`robustness_points: [300, 400, 500, 600]` was written to answer.
Applied to the best-of-6-sessions TTFA per vendor, marginal
per-gate survivors:

| threshold | marginal survivors | vendors |
|---:|---:|---|
| < 300 ms | 0 | — |
| **< 400 ms (pre-registered)** | **0** | — |
| < 500 ms | 1 | ElevenLabs (461 ms S4) |
| < 600 ms | 2 | + Cartesia (529 ms S1a) |

Discrimination starts at 500 ms (one survivor) and expands to two
at 600 ms; the 400 ms gate is inside the flat "everybody fails"
zone. The sweep is the pre-registered way to publish this without
amending the gate post-hoc.

**Why the gate fails everyone at 400 ms**: 400 ms was chosen as
headroom below the 500-600 ms perception threshold from the spec's
A.1 literature review. The measurements come from a **residential
Windows 11 client** with vendor endpoints resolved to whatever
the DNS returned that session (see F-11 for the client-side
parsimony discussion). The vendors' own SDKs / datacenter-local
tests likely produce lower numbers; we don't have that data.

**What we do about it**:
- We do NOT amend the gate post-hoc (that would defeat pre-registration)
- We do NOT claim any vendor "passed the 400 ms TTFA gate" — nobody did
- We DO report the per-vendor measured p50 / p90 as a **comparative
  ranking** for the residential-client venue, with F-11's scope
  disclaimer attached
- We DO publish the pre-registered sweep above so the discrimination
  threshold is visible without amending anything
- The 500 ms framing that appears in Q1 and F-11 discussion
  paragraphs is the perception-threshold *reference point*
  (spec A.1), not the pre-registered gate. The pre-registered
  gate is 100 ms tighter than the perception reference for
  reasons documented in gates.yaml rationale, and ElevenLabs —
  the "winner on latency" — fails the pre-registered gate in
  every session

**What this does NOT change**:
- **Vendor ranking on TTFA is stable**: ElevenLabs consistently
  faster than the rest (see F-11); Deepgram / Cartesia consistently
  slower than ElevenLabs but faster than OpenAI in the two
  sessions (S1a + S1b) they were measured
- Q1's real-time-voice guidance now reads "no measured vendor
  cleared the pre-registered 400 ms gate; ElevenLabs got closest
  at 461 ms (S4) and cleared the softer 500 ms perception
  reference in 5 of 6 sessions (S3 alone breached at 816), so it
  is descriptively-close-but-not-guaranteed against the perception
  reference under session-to-session variance"

Every latency-mode Deepgram row in `analysis/latency-*/latency.json`
shows p50 = 564-583 ms, p90 = 670-674 ms.

### <a name="wer-gate-admission"></a>WER-gate admission: every vendor fails at 5% agreement error rate

The `failure_incidence_pct < 2.0` conversational gate is applied
against the `wer_failure.agreement_error_rate_threshold` = **5%**
per-item threshold in `gates.yaml`. Every vendor produces 61-73%
of items over that threshold. The gate as pre-committed is
non-discriminating — it fails everyone.

**Why the gate fails everyone**: F-2 documents that wav2vec2 (our
second judge, chosen for architectural independence from Parakeet)
inflates absolute WER on synthetic speech. jiwer's normalisation
is lossy on some tokens (F-3 article-drop hard-coded as errors).
The 5% threshold was chosen from human-speech ASR literature; it
turns out to be at least an order of magnitude too tight for
TTS-vs-ASR agreement measured with this judge pair. The
**relative** ranking across vendors is preserved (Orpheus is
categorically worse than the pack — 26.89% vs 13.7-16.7%) and is
what we publish. The **absolute** thresholds in gates.yaml were
falsified as decision rules on this data.

**What we do about it**:
- We do NOT amend the gate post-hoc (that would defeat pre-registration)
- We do NOT report "vendor X passed the WER gate" — nobody did
- We DO report the per-vendor WER as a **comparative band** only
  (glossary reminder: `WER` in this doc is relative-ranking, never
  an absolute claim of intelligibility)
- The gate is retained in [`configs/gates.yaml`](../configs/gates.yaml)
  as pre-registration evidence and as a receipt that a specific
  pre-committed rule failed on this data. Amending it to something
  the data supports is a v2 workstream — the honest v1 result is
  "the threshold is broken as an absolute rule; the ranking under
  it is real"

**What this does NOT change**:
- The WER rankings in the [full per-provider tables](#full-per-provider-results)
  above hold (relative-ranking-only)
- No pass/fail claim in the memos or the case study depends on
  a WER-gate outcome; all quality decisions are made on
  Audiobox/DNSMOS with the SE(diff) test, not on WER
- F-3 tracks the specific gate design lessons (WER coloring
  removed from result tables because "green vs red" implies an
  absolute pass/fail claim we can't back)

**Gate outcomes JSON**: derived from
[`analysis/campaign-20260809T204608Z/wer.json`](../analysis/campaign-20260809T204608Z/wer.json)
(band counts + failure incidence per provider/use-case),
[`analysis/campaign-20260809T204608Z/hygiene.json`](../analysis/campaign-20260809T204608Z/hygiene.json)
(clipping + noise-floor per-vendor + long-stratum gate flags —
the hygiene gates fail Cartesia + Speechify on conversational
clipping and Cartesia + Google + Speechify on narration
long-stratum clipping, per the rows above), and
[`analysis/campaign-20260809T204608Z/acceptance.json`](../analysis/campaign-20260809T204608Z/acceptance.json)
(the file-level *acceptance* check on duration / LUFS / VAD /
character sanity — 1200 files, 1200 pass; this is upstream of
the hygiene gates and is not what "hygiene gates discriminate"
was meant to say).

### <a name="gate-robustness-sweep"></a>Gate-robustness sweep

The four-component scoring model in
[02 § 5](02_METHODOLOGY.md#5-pre-committed-hard-gates--tie-band-ranking-not-a-weighted-composite)
lists the sweep as the second pre-registered component after the
gates themselves. Each gate in
[`configs/gates.yaml`](../configs/gates.yaml) carries an explicit
`robustness_points` list — spec §5 / defect 3.40 flagged that a
±20% envelope on 400 ms tops out at 480 ms and never reaches the
500-600 ms perception threshold the gate's rationale cites, so
the sweep uses named points per gate.
[`src/veval/score/robustness.py`](../src/veval/score/robustness.py)
implements it; `veval score` writes the output to
[`analysis/campaign-20260831T175358Z/score.json`](../analysis/campaign-20260831T175358Z/score.json).

The score.json field `robustness[*].survivors_per_point` reports
the **full-intersection** survivor set (a provider must pass
*every* other gate too) at each swept threshold. The TTFA and
RTF admission subsections above report the **per-gate marginal**
sweep — how many vendors' measurement clears just that gate at
each threshold, in isolation. Both framings are useful and both
are traceable to the same source data.

**Trap in the receipt's own summary flag**: score.json's
`is_stable` field is set from the intersection sweep, not the
marginal one. All four conversational gates in the receipt read
`is_stable: true` with zero survivors at every swept point —
which sounds like "threshold-insensitive" but is actually the
intersection collapsing (the WER gate fails all 8 regardless of
which point the sweep is at, so the intersection is zero at
every point, so the flag reads stable). The marginal TTFA sweep
above is 0 → 0 → 1 → 2 at 300/400/500/600 ms — anything but
flat. Same shape for the R3 conversational clipping gate, which
6 of 8 vendors clear marginally (only Cartesia + ElevenLabs
fail) yet reads `is_stable: true` at its single sweep point
because the WER + zero-tolerance gates keep the intersection at
zero. **A reader opening the score.json should treat `is_stable`
as an intersection property, not evidence that any single gate
is threshold-insensitive** — the per-gate marginal tables in
this section are the answer to that question.

Third gate that carried a nontrivial sweep — narration
`long_stratum_acoustic_noise_floor_dbfs`, `robustness_points:
[−30, −40, −50]` on the worst-of-8 long-stratum reading per
vendor. Computed on the R3 campaign
(`campaign-20260831T175358Z/hygiene.json`), which is what the
committed score.json sweeps:

| threshold | R3 marginal survivors | R3 vendors | R2 marginal survivors |
|---:|---:|---|---:|
| ≤ −30 dBFS | 7 | all except Orpheus (−27.75) | 8 (all pass) |
| **≤ −40 dBFS (pre-registered)** | **5** | Deepgram, Fish, Google, OpenAI, Speechify | 6 (adds Orpheus, which R2 measured at −52.78 before the R3 truncation-tail shift; drops nobody) |
| ≤ −50 dBFS | 3 | Fish, OpenAI, Speechify | 2 (OpenAI + Orpheus) |

The 5-vendor R3 survivor set at −40 dBFS matches the R3 gate
outcome in the narration table above (which also fails Cartesia,
ElevenLabs, and Orpheus on the worst-of-8 long-stratum reading).
R2 gives 8 / 6 / 2 — a visibly different shape because Orpheus's
worst-of-8 long-stratum reading shifted from −52.78 in R2 to
−27.75 in R3 (F-12 area; most likely a truncation-tail artefact
on the 14.59-s cap). Discrimination at −40 is not an artefact
of the exact threshold in either round: −30 adds only Cartesia +
ElevenLabs back in on R3; −50 drops Deepgram + Google.

Fourth gate that carried a nontrivial sweep — conversational
`failure_incidence_pct`, `robustness_points: [1.0, 2.0, 5.0]`:

| threshold | marginal survivors | vendors |
|---:|---:|---|
| < 1.0 | 0 | — |
| **< 2.0 (pre-registered)** | **0** | — |
| < 5.0 | 0 | — |

Genuinely flat: on R3 every vendor lands between 64.0% (Fish, the
floor) and 78.4% (Orpheus, the ceiling); on R2 between 61.3%
(Fish + Speechify at the floor) and 73.3% (Orpheus). No vendor
in either round clears even the loosest 5.0 sweep point. The
sweep is the strongest statement of "the WER gate is broken as
an absolute rule on this data": not just non-discriminating at
2.0, but non-discriminating across the full pre-registered sweep.
F-2 documents the two-judge-inflation mechanism; the sweep is
the receipt.

Gates whose sweep was flat by design (`robustness_points: [0.0]`
— clipping gates and the commercial-use gate) reflect that zero
is pre-committed as non-negotiable; the flatness is by design,
not a missing measurement.

---

## <a name="verification-pack-outcomes-phase-2c"></a>Verification pack outcomes (Phase 2c)

**This is the index of what T1–T8 and N1–N2 mean.** All references
to a "T-test" or "N-test" elsewhere in the documentation point back
to this table. Each test has a per-test evidence file
(hypothesis + method + criterion + result + verdict) linked in the
`Evidence` column.

The verification pack had 10 tests on the roster (T1..T8, N1, N2).
T3 was retired mid-project (the 2b DNSMOS run answered its exit
criterion before Phase 2c even started), leaving 9 active tests.
Table below shows all 10 rows with T3's retirement noted:

| # | Outlier | Vendor | Verdict | Evidence |
|---|---|---|---|---|
| T1 | Clipping 429/406 samples (100× next) | Cartesia | **Confirmed** (via F-4a — 2nd independent pipeline) | [T1](../analysis/verification/T1_cartesia_clipping.md) |
| T2 | WER ~27% (2× next) | Orpheus | **Answered by T8** — 14.59s output cap = mechanical incompletion | [T2](../analysis/verification/T2_orpheus_wer.md) |
| T3 | Narration PQ 7.41 conv → 8.00 narr | Orpheus | **Retired** — DNSMOS #2 narr confirms direction, satisfies exit criterion | (retired) |
| T4 | L03 monotonic fadeout (3.6 dB) | ElevenLabs | **Confirmed with refinement** — 3/3 fresh regens fade monotonically; mean delta 2.7 dB, not 3.6 dB | [T4](../analysis/verification/T4_elevenlabs_L03_fadeout.md) |
| T5 | Latency 736/956 ms (2× next; original observation from campaign-cached row) | OpenAI | **Confirmed (slower than ElevenLabs)** — S3 = 1369/1882 ms, all 3 sessions consistently slower than ElevenLabs. Session-to-session absolute values not stable (F-11). | [T5](../analysis/verification/T5_openai_latency.md) |
| T6 | Audiobox #1 both UC | Speechify | **Confirmed with reversal** — alt voice edmund_32 scores +0.30 higher on conv (cross-gender: geffen_32 female → edmund_32 male, +6.05σ) and +0.10 higher on narr (same-gender: wyatt_32 male → edmund_32 male, +4.02σ); still #1 of 9 on both use cases | [T6](../analysis/verification/T6_speechify_voice_bias.md) |
| T7 | Fastest TTFA (439/479 ms in S1; original observation) | ElevenLabs | **Confirmed faster than OpenAI**, all 6 sessions. Sub-500 ms p90 held in 5 of 6 sessions (S1a 479, S1b 474, S2 469, S4 461, S5 468); S3 alone breached at 816 ms. F-11 documents the session-to-session variance. | [T7](../analysis/verification/T7_elevenlabs_ttfa.md) |
| T8 | "Cheapest $0.030/1K" (headline claim from `cost_model.json`) | Orpheus | **Refuted with two bigger findings** — (a) 14.59s hard output cap, cost is fixed-per-call not linear-with-text; (b) the $0.030 itself is a `cost_model.py` default-assumption artefact, honest per-1K-words is ~$0.067-0.088 (peer-priced to OpenAI). See T8 for the full analysis. | [T8](../analysis/verification/T8_orpheus_cost.md) |
| N1 | Audiobox #8/#8 vs DNSMOS #1/#1/#2 narr | OpenAI | Pending (manual listen) | [N1](../analysis/verification/N1_openai_narration_inversion.md) |
| N2 | DNSMOS OVRL+SIG #8/#8 conv | Fish | **Confirmed** — Fish noise floor +12.6 dB above 8-vendor median (2× threshold); DNSMOS ONNX + hygiene analyzer are two independent code paths agreeing on the same defect. | [N2](../analysis/verification/N2_fish_conv_dnsmos.md) |

**Verdict tally (10 rows):**
- **Confirmed cleanly**: 3 (T1, T7, N2)
- **Confirmed with refinement / caveat / reversal**: 3 (T4, T5, T6)
- **Answered by another test's finding**: 1 (T2, resolved by T8)
- **Refuted with a bigger finding**: 1 (T8)
- **Retired mid-project**: 1 (T3)
- **Pending manual work**: 1 (N1)

Total Phase 2c spend: **~$0.63** across the T4/T6/T8 fresh regens,
2 verification latency sessions (T5+T7), plus **1 additional latency
session with concurrent ping baseline** (Wave 4b, 2026-08-12,
~$0.02) that surfaced the S3 shift refuting the T7 stability
sub-finding — see
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11).

---

## Decision framework (three questions)

Answer these in order. Only proceed once the previous question has
a clear answer for your use case.

### Q1 — Hard constraints

- **Any turn ≥ 15s?** Orpheus is out (14.59s output cap).
- **Any downstream ASR / MOS / resample pipeline?** Cartesia needs a
  −1 dBFS peak-limiter first, or accept ~46% loss to DNSMOS refusals on R2 (41.3% on R3 — pooled across both use cases; see footnote ² above for the per-cell breakdown).
- **Real-time-voice latency ceiling?** Two thresholds to keep
  straight: the **pre-registered gate is `ttfa_p90_ms < 400`**
  (`configs/gates.yaml`, chosen as headroom below the 500-600 ms
  perception threshold), and the **perception-threshold reference
  from the literature is ~500 ms** (spec A.1).
  - Against the pre-registered 400 ms gate: **no measured vendor
    passes.** ElevenLabs Flash's best measurement was 461 ms p90
    (S4); Cartesia 529 ms; Deepgram 670 ms; OpenAI 946 ms. Every
    measured streaming vendor fails the pre-committed gate in
    every session it was measured. See [TTFA-gate admission](#ttfa-gate-admission).
  - Against the softer 500 ms perception reference: ElevenLabs
    Flash cleared it in **5 of 6 sessions** (S1a 479, S1b 474, S2
    469, S4 461, S5 468 — all under 500 ms p90) and failed only
    in S3 (816 p90) — no other vendor cleared 500 ms in any
    session; see F-11.
  - **Speechify / Fish / Google / Orpheus** are unmeasured on
    streaming TTFA (their adapters don't stream); they may or
    may not meet either bar — *unknown*, not *disqualified*.
  - For a real-time deployment: **measure from your own
    environment across ≥5 sessions** with client-side event-loop
    lag logged (F-11), and expect 50-90% session-to-session
    variance from residential clients. Do not provision from any
    of the numbers above as a ceiling.
- **Byte-identical caching?** Impossible with any of the 8; save the
  audio yourself.

### Q2 — Which "quality" matches your users?

Audiobox's two axes measure different constructs, per F-8:

- **Cleanliness / technical audio quality** (both AB.PQ and DNSMOS
  measure a version of this — see F-8 for the per-pair ρ). If your
  use case is enterprise IVR / accessibility / transactional voice
  → **OpenAI** ties for #1 on DNSMOS OVRL on both use cases (0.7–1.3σ
  vs the tied competitor, not significant — no vendor cleanly "wins"
  DNSMOS at n=75). **Speechify wins the parallel PQ measure** by
  3.7σ (conv) / 7.0σ (narr vs Cartesia — 9.5σ if Orpheus is retained).
  So the "cleanliness" answer depends on which cleanliness rater
  you trust more; OpenAI dominates one, Speechify the other. **On
  cost**: OpenAI ($0.075 / 1K words) is 34% of ElevenLabs' price
  ($0.22, tied on conv OVRL) and 50% of Deepgram's ($0.15, tied on
  narr OVRL) — **50-66% saving** on tied-on-DNSMOS quality.

- **Warmth / engagement / aesthetic content-enjoyment** (AB.CE only —
  it's the axis that anti-correlates with DNSMOS at ρ ≈ −0.5, see
  F-8) → **Speechify** leads AB.CE on both use cases (5.9σ conv vs
  Fish, 7.3σ narr vs ElevenLabs). Speechify at **$0.10 / 1K words
  (100K/mo tier)** is the cheaper of the top-2 CE vendors; at 10K/mo
  Speechify is $1.00/1K (the Starter subscription over
  a low volume) — much more expensive per word than OpenAI's
  pay-per-use $0.075. ElevenLabs at $0.22 (100K/mo) is the #2 CE
  vendor on both use cases and 2.2× Speechify's price. Orpheus's
  nominal $0.030 in the table is a `cost_model.py` artefact under
  a 100-word-per-call default that predates T8's per-call
  output-cap measurement; the honest Orpheus price is
  **~$0.067-0.088/1K words** (see the ⚠ block under
  [Cost calculus](#cost-calculus)) — **peer-priced to OpenAI**,
  not category-crushing cheap.

**AB.PQ is the cleanliness axis, AB.CE is the warm axis**
(agrees with / anti-correlates with DNSMOS respectively; see
F-8). Speechify wins both, so Speechify is a two-axis Audiobox
winner and ambiguous on DNSMOS. See the Rankings summary above
for the per-comparison SE(diff) figures.

### Q3 — Is #1 quality worth the cost premium over #2?

Look at the Rankings summary above. Each pair reports
`|Δ| / SE(diff)`:

- Under **1.96σ** → statistically tied at α=0.05; the difference
  is not measured precisely enough to be distinguishable from zero.
  Pick the cheaper vendor on this axis.
- **2σ to 4σ** → borderline evidence that the ordering is real;
  the estimate is precise enough to be distinguishable from zero
  but not by much. σ measures precision of the *estimate*, not
  audible size of the *gap* — see caveats below.
- **Over 4σ** → strong evidence the ordering is real (estimate is
  many SEs from zero). Still not a claim about perceptual
  magnitude; a 6σ result on a 0.14/10 = 1.4%-of-scale delta
  means "we're certain the delta is not zero," not "the delta
  is audibly large."

**Statistical caveats you should know before quoting these σ
ratios**: (a) multiplicity is not corrected — Bonferroni for 8
tests would move OpenAI/ElevenLabs conv OVRL from 2.0σ paired
back to a tie; (b) σ measures precision of the *estimate*, not
perceptual size of the *gap*; the 3.7σ Speechify Audiobox lead
is a 0.14/10 = 1.4% delta on scale; (c) the multi-rater BT panel
that would map score-delta to listener-preference-share was
deferred to v2. Full write-up in the
[Statistical caveats section](#statistical-caveats-multiplicity-effect-size-perceptual-calibration)
above.

Full plain-language walkthrough in
[05_CASE_STUDY.md § "What this means for a PM"](05_CASE_STUDY.md#what-this-means-for-a-pm-buying-voice-ai).

---

## <a name="glossary"></a>Glossary

- **AB.PQ** — Meta Audiobox Aesthetics *production_quality* axis
  (0–10). Meta describes this as **technical cleanliness / perceived
  audio quality** (pleasant timbre, no distortion). F-8 shows PQ
  agrees with DNSMOS's cleanliness axes (mean ρ +0.238 conv,
  +0.571 with p808) — it's a cleanliness axis, not a warm-rater
  axis.
- **AB.CE** — Meta Audiobox Aesthetics *content_enjoyment* axis
  (0–10). This is the axis that behaves like a warm/aesthetic
  rater — it anti-correlates with DNSMOS in both use cases
  (mean ρ −0.506 conv, −0.375 narr). See
  [06 § F-8](06_KEY_FINDINGS.md#f-8) for the per-pair ρ receipt.
- **DN.p808** — Microsoft DNSMOS *p808_mos* — ITU-T P.808 overall
  MOS from a single-model predictor (1–5).
- **DN.ovrl** — Microsoft DNSMOS *ovrl_mos* — ITU-T P.835 overall
  MOS from a three-scale predictor (1–5).
- **DN.sig** — Microsoft DNSMOS *sig_mos* — P.835 speech-signal
  quality (1–5).
- **DN.bak** — Microsoft DNSMOS *bak_mos* — P.835 background-noise
  intrusiveness (higher = less intrusive, 1–5).
- **clip samples** — Total audio samples with amplitude ≥ ±1.0 across
  all 75 files. Direct sample-peak detection in the hygiene analyzer
  (numpy-based, not pyloudnorm — pyloudnorm is used for LUFS
  loudness only).
- **noise floor (dBFS)** — Mean noise floor across 75 files (hygiene
  analyzer, `pyloudnorm.integrated_loudness` on the quiet-window
  windows). Less-negative = noisier.
- **WER %** — Mean `agreement_wer` across all 75 items per vendor.
  `agreement_wer` per item = `jiwer.wer(reference, agreed_hypothesis)`
  where `agreed_hypothesis` is the string of tokens both judges
  (wav2vec2 + faster-whisper) emitted at the same position; disputed
  tokens are omitted from `agreed_hypothesis` and therefore counted
  as errors against the reference — conservative. **Reported as
  relative-ranking-only**: absolute WER is inflated because wav2vec2
  systematically drops articles that Whisper preserves, so every
  article is a disputed token and hard-coded into the error count
  (see F-2 for the resulting artifact). Relative rankings survive
  only under the assumption that the article-drop rate is
  approximately constant across vendors — untested; caveat.
- **TTFA p50 (ms)** — Time-to-first-audio-frame, 50th percentile,
  50-trial session, S01 corpus. **Residential Windows 11 measurement — absolute values are one
  point in a session-to-session distribution (see F-11); not
  upper bounds.**
- **$/1K words** — Cost per 1,000 words at the specified monthly
  volume tier (see full cost table).

Full measurement methodology in
[02_METHODOLOGY.md](02_METHODOLOGY.md).

---

## Reproducing these numbers

```powershell
# --- Analyzer replay from the primary campaign + variance runs ---
uv run veval analyze campaign-20260809T204608Z --stages all
uv run veval analyze variance-20260809T205319Z --stages quality

# --- Latency: all 6 sessions (S1a + S1b + S2 + S3 + S4 + S5) ---
# S1a + S1b (2026-08-09) — first-day pair, 50 trials × 4 streaming vendors
uv run veval analyze latency-20260809T214106Z --stages latency
uv run veval analyze latency-20260809T222356Z --stages latency
# S2 (2026-08-11) — second pass, adds T5/T7 verification
uv run veval analyze latency-20260811T183028Z --stages latency
uv run veval analyze latency-20260811T183202Z --stages latency
# S3 (2026-08-12) — third pass with concurrent ping baseline.
# The concurrent ping-baseline log is committed at
# `analysis/ping-baseline-20260812T191138Z.jsonl` (274 probes to
# Cloudflare 1.1.1.1); the audio runs/ are regenerable per 03.
uv run veval analyze latency-20260812T191143Z --stages latency  # OpenAI, 50/50
uv run veval analyze latency-20260812T191323Z --stages latency  # ElevenLabs, 40/50 (spend-cap)
# S4 + S5 (2026-09-01, Phase 2 Follow-up 3) — same-day pair
uv run veval analyze latency-20260901T185715Z --stages latency  # S4 ElevenLabs
uv run veval analyze latency-20260901T190715Z --stages latency  # S4 OpenAI
uv run veval analyze latency-20260901T191000Z --stages latency  # S5 ElevenLabs
uv run veval analyze latency-20260901T201051Z --stages latency  # S5 OpenAI (T19:10 attempt crashed, this is the T20:10 rerun)

# --- Cross-metric analysis + per-comparison SE(diff) + paired test ---
uv run veval analyze campaign-20260809T204608Z --stages cross_metric
uv run python scripts/_noise_floor_recompute.py    # per-vendor SE + unpaired ties
uv run python scripts/_paired_test.py              # paired vs unpaired

# --- Regenerate the figures ---
uv run python scripts/generate_figures.py
```

**Regenerating audio runs from scratch**: `runs/` is gitignored
(regenerable + large — ~5 GB per full campaign). To reproduce
audio, follow [03_RUNBOOK.md § generate](03_RUNBOOK.md); the
`analyze` invocations above assume those `runs/` directories
have been produced locally or restored from a snapshot.

See [03_RUNBOOK.md](03_RUNBOOK.md) for full install + reproduce
instructions.
