# 04 · Results Summary

*Full per-provider measurements across 8 vendors × 2 use cases,
plus the verification-pack verdicts and the cost calculus a
decision-maker needs.*

> **⚠ Scope disclaimer** · Results as of 2026-08-12 on specific
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

**Important scope note (cache-only campaign)**: the campaign run
`campaign-20260809T204608Z` **ran fully from the content-hash
cache** — every audio file it "produced" was replayed from bytes
generated at an earlier, unrecorded date. This is why:

- Latency's `n_fresh = 0` and `n_with_ttfa = 0` for every vendor
  in [`analysis/campaign-20260809T204608Z/latency.json`](../analysis/campaign-20260809T204608Z/latency.json)
  (the campaign has no timing data — TTFA / RTF come from the
  dedicated latency-mode sessions instead).
- No `synthesis_time` is available, so **RTF was not adjudicated
  in v1** — see the [RTF admission](#rtf-admission).
- Combined with F-1 (nothing is byte-reproducible), **each cell
  is a frozen single draw whose exact synthesis date is not
  recorded in `runs/<id>/manifest.json`** — only the cache-hit
  timestamp is. The published-date-on-every-finding discipline
  in 02 is genuine at the *analysis-artefact* level but degrades
  at the *raw-audio-generation* level for cache-hit rows.
- The RTF gate row therefore reports "not adjudicated" rather
  than pass/fail. All quality-axis and hygiene claims are
  unaffected — they read audio bytes, not timestamps.

A v2 pass would re-run the campaign with `--no-cache` to get
per-item `synthesis_time` and adjudicate RTF; see
[07_GAPS_AND_FUTURE_WORK.md § Deferred by scope](07_GAPS_AND_FUTURE_WORK.md#deferred-by-scope-not-attempted-in-v1).

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

### Conversational

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
<td><b>cartesia</b></td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 7.44</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 5.96</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.89</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.25</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.48</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.13</td>
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

### Narration

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
<td><b>google</b></td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 7.97</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 6.44</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 4.02</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 3.35</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 3.60</td>
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 4.11</td>
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
hard output cap (F-9 T8, stdev 0.000s across 8 items). The
reference texts for narration items are ~90 seconds of expected
speech, so **~16% of the expected duration is what got scored**.
Every marked-¹ cell was computed on structurally incomplete audio.
The dramatic −78.7 dBFS noise floor is not "cleaner speech" — it's
mostly silence padding the truncated clips out. Treat any "Orpheus
wins narration X" reading as an artifact of the truncation, not
a signal about the model's audio quality on complete output.

**Footnote ² (Cartesia narration DNSMOS)**: 37 of 75 Cartesia
narration clips (49%) were refused by DNSMOS for peak_out_of_range
(F-4a). The four DNSMOS columns for Cartesia narration are
computed on the 38 surviving clips — a **survivor-selected subset**,
not the full column. Even so, Cartesia's DNSMOS ranks on the
surviving subset are still #8 of 8 on OVRL / SIG / BAK — the
mastering signature that got the other 37 refused persists in the
38 that made it through.

<a name="footnote-3-deepgram-conversational-ttfa"></a>
**Footnote ³ (Deepgram conversational TTFA)**: the 583 ms figure
in this table is from a campaign-mode Deepgram row. The two
dedicated latency-mode sessions on 2026-08-09 (n=50 trials each,
serial) measured Deepgram at **p50 = 583 / 564 ms, p90 = 674 / 670
ms** — statistically consistent with the campaign value. **The
prior "Deepgram ~180 ms p50 / ~230 ms p90" claim that appeared in
earlier drafts of this footnote and in T5 / T7 is retracted — no
run in `analysis/latency-*/latency.json` measures Deepgram under
500 ms.** The origin of the ~180 ms number is unclear (possibly a
Deepgram-side self-reported metric misread as wall-clock TTFA, or
a pre-measurement expectation that was never verified against the
harness data); regardless, it is not supported by any measurement
in this repository. Deepgram wasn't re-measured in S2/S3, so we
have two consistent latency-mode sessions from the same day, not
three days of data.

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

## Rankings summary

**Top-2 per quality axis per use case** — the "who's actually
worth paying for?" table. Each pair is judged **significant** iff
`|Δ| > 1.96 × SE(diff)` where `SE(diff) = √(SE_a² + SE_b²)` and
`SE_i = SD(vendor's 75-item column) / √75`. This is the standard
normal-approximation test at α=0.05. Per-vendor per-signal SDs +
SE_mean values are in [`scripts/_noise_floor_recompute.py`](../scripts/_noise_floor_recompute.py)
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
| Audiobox PQ (warm) | speechify | 7.897 | elevenlabs | 7.755 | +0.142 | **3.7σ** | **SIG_DIFF** |
| Audiobox CE (warm) | speechify | 6.462 | fish | 6.242 | +0.220 | **5.9σ** | **SIG_DIFF** |
| DNSMOS OVRL (clean) | openai | 3.489 | elevenlabs | 3.467 | +0.022 | 1.3σ | **TIE** |
| DNSMOS SIG (clean) | openai | 3.697 | elevenlabs | 3.686 | +0.011 | 0.8σ | **TIE** |

### Narration

Orpheus is **excluded from #2 in the top-1-vs-top-2 slot** for
narration because its narration audio is truncated to ~16% of the
expected reading duration by the model's 14.59-second per-call
output cap (F-9 T8). Its narration mean is a mean over structurally
incomplete audio — any "Orpheus wins narration X" is an artifact
of the truncation, not a listener signal. The Speechify-vs-Orpheus
comparison is preserved as a lower row for transparency, footnote ¹,
but the load-bearing top-1-vs-top-2 σ ratio uses Cartesia (honest
#2) instead.

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | \|Δ\|/SE(diff) | Verdict |
|---|---|---:|---|---:|---:|---:|---|
| Audiobox PQ (warm) | speechify | 8.150 | cartesia² | 7.986 | +0.164 | **7.0σ** | **SIG_DIFF** |
| Audiobox CE (warm) | speechify | 6.662 | elevenlabs | 6.466 | +0.197 | **7.3σ** | **SIG_DIFF** |
| DNSMOS OVRL (clean) | openai | 3.463 | deepgram² | 3.442 | +0.021 | 1.1σ | **TIE** |
| DNSMOS SIG (clean) | openai | 3.679 | deepgram | 3.677 | +0.002 | 0.2σ | **TIE** |

*Transparency row (Orpheus not excluded):*

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | \|Δ\|/SE(diff) | Verdict |
|---|---|---:|---|---:|---:|---:|---|
| Audiobox PQ (warm), Orpheus not excluded | speechify | 8.150 | orpheus¹ | 8.002 | +0.148 | 9.5σ | (artifact — see ¹) |
| DNSMOS OVRL (clean), Orpheus not excluded | openai | 3.463 | orpheus¹ | 3.453 | +0.010 | 0.7σ | (artifact — see ¹) |

¹ Orpheus's narration audio is truncated. The 9.5σ number is a
mechanical property of the truncated audio distribution having
low variance under the vendor's fixed-length output cap, not a
listener signal. It sat in earlier drafts of this table before
T8 established the truncation; carried below the primary table
as a receipt that "9.5σ" was later reinterpreted as an artifact,
not as evidence of a listener effect.

² Cartesia (honest AB.PQ #2) and Deepgram (honest DNSMOS OVRL #2)
are the correct top-1-vs-top-2 opponents once Orpheus is excluded.

**Interpretation:** all four Audiobox top-1-vs-top-2 comparisons
are meaningfully different — Speechify's warm-rater lead over the
honest #2 vendor is **3.7σ to 7.3σ significant** (not 9.5σ; that
was the artifact-inclusive figure and is retired from the headline
range). All DNSMOS top-1-vs-top-2 comparisons are ties — OpenAI's
DNSMOS "win" is essentially indistinguishable from ElevenLabs
(conv), and from Deepgram (narr, once Orpheus is excluded).

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
(≈ 2.73σ). All four Audiobox SIG_DIFF calls (3.7σ – 7.3σ unpaired;
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
existing `veval rate build/score` pipeline (already implemented in
`src/veval/rate/`) with 15–30 blinded raters and compare BT
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
narr) as measured across the 144 items with valid reference
transcripts. That means **every char-billed vendor's $/1K words in
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
| **speechify** | 0.100 | **0.100** | **0.040** | Starter $10/mo covers 100K; scales well at 1M+. Char-billed. |
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

Both derivations land in the **~$0.070-0.088/1K words** band, not
$0.030. Prior drafts of this section wrote the derivation as "150
items × $0.003 = $0.45 ÷ 15K words = $0.030/1K words" — the "15K
words" in that arithmetic came from cost_model.py's projected
words-per-month at 100K wpm/mo × 5.0/500 scaling, not from the
actual campaign corpus (which is 6,651 words across 144 items with
valid references). Neither derivation reconciles with an as-generated
per-word cost, because the pipeline used one call per item (not one
call per 100 words); it just so happens that on the observed corpus
the as-generated cost is $0.45 / 6.651K words = **$0.068/1K words**,
close to the T8-based rendered-audio estimate.

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
cost_model.json (auditability — the model artefact IS the number
the pipeline produced), with the † footnote and this ⚠ block as
the receipt for what it actually represents. **Do not compare
$0.030 against ElevenLabs' $0.22 as if they were peer prices** —
they are not derived on comparable assumptions. Neither survives
the Q1 hard-constraint check for real narration anyway (Orpheus
is out on Q1 because of the 14.59-s output cap; see § Decision
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

## Latency (3 sessions on 3 dates spanning 4 days, with concurrent ping baseline on S3)

Time-to-first-audio-frame (TTFA), 50 serial trials per session,
conversational S01 corpus item. Three independent sessions across
2026-08-09, -11, -12. **Session 3 was run with a concurrent
ping-to-1.1.1.1 baseline** (274 probes during the S3 window) to
separate vendor variability from local ISP jitter.

| Vendor | S1 p50 / p90 | S2 p50 / p90 | S3 p50 / p90 | Range across 3 sessions |
|---|---|---|---|---|
| **elevenlabs** (Flash v2.5) | 439 / 479 | 424 / 469 | **694 / 816** | p50: 424–694 ms (+64% max shift) |
| openai (tts-1-hd) | 736 / 956 | 936 / 1493 | **1369 / 1882** | p50: 736–1369 ms (+86% max shift) |
| deepgram | 583 / 674 (S1a); 564 / 670 (S1b) | not re-measured | — | — |
| cartesia | 467 / 529 (S1a); 468 / 530 (S1b) | not re-measured | — | — |
| speechify · fish · google · orpheus | not applicable* | | | |

**Every measured streaming vendor's p90 exceeds the pre-registered
400 ms `ttfa_p90_ms` gate** in every session in which they were
measured. ElevenLabs at 479 ms (S1 low) is the closest to the
threshold but still failed. See the
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

**Table caveat**: ElevenLabs S3 landed 40/50 trials before the
pay-per-1K-chars spend cap tripped (S1/S2 were on Creator credits,
unaffected). n=40 is fine for p50/p90 (SE of p90 ≈ 40 ms at this
magnitude, small vs. the +58% S1→S3 shift). Anything past p90 for
S3 is under-sampled.

**Portable finding** (revised — see F-11 for the retraction of the
prior "stability" claim):

- **Vendor ranking on TTFA is stable**: ElevenLabs is consistently
  faster than OpenAI in every session (424/439/694 vs 736/936/1369
  on p50). The ordering is portable. Rank tests are robust at n=3.
- **Absolute TTFA is NOT stable** for either vendor. Both moved
  50-90% p50 session-to-session on our public-tier accounts.
  Neither vendor is "stable" in an operational sense; the initial
  ElevenLabs "sub-500 ms p90 reliably" finding held only in the
  first two sessions and was refuted by S3.
- **The observed variability is not our last-mile link.** The
  simplest single cause consistent with "both vendors slowed
  together on the same day" is **client-side** (local machine
  contention, one-shot background scan, Python event-loop stall).
  Vendor-side capacity is a candidate but not parsimonious for a
  simultaneous slowdown of two independent SaaS providers.
- **n=3 sessions cannot characterise the variance distribution.**
  Rank claims survive at n=3; stability claims need ≥5-10 sessions
  across ≥2 weeks with per-trial client-lag logging.

See [documentation/figures/f3_latency_stability.png](figures/f3_latency_stability.png)
for the 3-session visual with concurrent ping-baseline annotation.
Full retraction narrative in
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11-retraction-of-the-latency-stability-is-a-distinct-axis-finding).
Verdict details in
[analysis/verification/T5](../analysis/verification/T5_openai_latency.md)
and [T7](../analysis/verification/T7_elevenlabs_ttfa.md) (both
updated with S3 data).

### <a name="rtf-admission"></a>RTF (real-time factor) — not measured in v1

**RTF was pre-committed as the narration latency gate**
(`rtf ≥ 3.0`; see [`configs/gates.yaml`](../configs/gates.yaml))
but was **not measured per-vendor in v1**. The reasons:

- The campaign ran fully from content-hash cache (regenerating
  1200 audio files at every analyzer iteration would burn budget
  on identical outputs). Cached calls have no `synthesis_time` to
  divide the audio duration by.
- The dedicated latency sessions (S1/S2/S3) ran the S01
  conversational item, not long-narration items — RTF is a
  narration-workload metric and the sessions were designed for
  TTFA, not throughput.
- The
  [`latency.json`](../analysis/campaign-20260809T204608Z/latency.json)
  schema *does* have `long_stratum_rtf_p50` / `long_stratum_rtf_p10`
  fields; every row is `null` because
  `n_with_total = 0` on the cached campaign.

**Impact**: the pre-committed narration RTF gate cannot be
adjudicated on v1 data. Neither vendor is called out as
"failed RTF" or "passed RTF" in the results above — the gate is
`not adjudicated`, not `passed`.

**v2 workstream**: run a dedicated **narration-latency session**
(8 long items × 8 vendors × 1 draw = 64 fresh generations with
`synthesis_time` logged; ~$0.30 spend; ~30 min wall-clock).
Compute per-vendor `audio_duration_s / synthesis_time_s` per
long item; report `long_stratum_rtf_p10 / p50 / p90` per vendor
and pass/fail against `rtf ≥ 3.0`. Documented in
[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md).

---

## <a name="pre-registered-gate-outcomes"></a>Pre-registered gate outcomes

**Which pre-committed gates did each vendor pass or fail?** The
gates were frozen in [`configs/gates.yaml`](../configs/gates.yaml)
under `prereg-v1` before any results existed (git-tagged). Applying
them strictly, on the campaign data:

### Conversational gates (5 gates; each row states its own denominator)

| Gate | Threshold | Pass | Fail | Exempt / N/A | Fail admission |
|---|---|---:|---:|---:|---|
| `ttfa_p90_ms < 400` | streaming, 4 measured | **0** | **4** | 4 (na_policy = exempt-and-annotate) | **Every measured streaming vendor fails.** Best measurement: ElevenLabs S1 at 479 ms. All others (Cartesia 529, Deepgram 670-674, OpenAI 946-1882) fail more clearly. See [TTFA-gate admission](#ttfa-gate-admission) below. |
| `failure_incidence_pct < 2.0` (WER-based) | all 8 | **0** | **8** | 0 | **Every vendor fails.** Failure incidence 61.3% (Fish, Speechify) to 73.3% (Orpheus). See [WER-gate admission](#wer-gate-admission) below. |
| `clipped_samples == 0` | all 8 | 7 | 1 | 0 | Cartesia (429/406 clipped samples/item on average, F-4) |
| `acoustic_noise_floor_dbfs ≤ −40` | all 8 | 7 | 1 | 0 | Fish (noise floor above threshold, see N2) |
| `commercial_use_permitted == 1` | all 8 | 8 | 0 | 0 | All 8 vendors on paid tiers permit commercial use |

### Narration gates (4 gates; each row states its own denominator)

| Gate | Threshold | Pass | Fail | Exempt / not adjudicated | Fail admission |
|---|---|---:|---:|---:|---|
| `rtf ≥ 3.0` | streaming, throughput-bound | 0 | 0 | **8 (not adjudicated in v1)** | RTF not measured in v1. Campaign ran fully from content-hash cache (no `synthesis_time` on cached calls). Latency sessions ran conversational S01 only. `long_stratum_rtf_p50 / _p10` fields in [`latency.json`](../analysis/campaign-20260809T204608Z/latency.json) are `null` for every row (`n_with_total = 0`). Full explanation in [RTF admission](#rtf-admission) below. |
| `monotonic_quality_drift_flag == 0` | TTSDS2-based | 0 | 0 | **8 (n/a — TTSDS2 skipped per D-A)** | see [D-B decision block](06_KEY_FINDINGS.md#d-b) |
| `long_stratum_acoustic_noise_floor_dbfs ≤ −40` | hygiene, long items only | 7 | 1 | 0 | Fish (persistent noise floor) |
| `long_stratum_clipped_samples == 0` | hygiene, long items only | 7 | 1 | 0 | Cartesia |

### <a name="ttfa-gate-admission"></a>TTFA-gate admission: every measured streaming vendor fails at 400 ms p90

The `ttfa_p90_ms < 400` conversational gate is applied against
the pre-registered threshold in
[`configs/gates.yaml`](../configs/gates.yaml). The rationale
committed with the gate is: "Perception degrades above ~500-600 ms
(spec A.1); 400 ms is a deliberate headroom margin below that,
since TTS latency is only one term in an agent's end-to-end
budget (LLM + TTS + network)."

Measured p90 by vendor and session (best measurement in bold):

| Vendor | S1 p90 | S2 p90 | S3 p90 | Best measured | Gate |
|---|---:|---:|---:|---:|---|
| ElevenLabs Flash v2.5 | 479 / 474 | 469 | 816 | **469 ms** (S2) | **FAIL** — closest to threshold |
| Cartesia | 529 / 530 | (not re-measured) | — | **529 ms** (S1a) | **FAIL** |
| Deepgram Aura-2 | 674 / 670 | (not re-measured) | — | **670 ms** (S1b) | **FAIL** |
| OpenAI tts-1-hd | 956 / 946 | 1493 | 1882 | **946 ms** (S1b) | **FAIL** |
| Speechify · Fish · Google · Orpheus | not applicable — adapters don't stream | | | | exempt (na_policy = exempt-and-annotate, see D-008) |

**Every measured streaming vendor fails the pre-registered gate.**
The gate as committed is non-discriminating on this data.

**Why the gate fails everyone**: 400 ms was chosen as headroom
below the 500-600 ms perception threshold from the spec's A.1
literature review. The measurements come from a **residential
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
- The 500 ms framing that appears in Q1 and F-11 discussion
  paragraphs is the perception-threshold *reference point*
  (spec A.1), not the pre-registered gate. Prior drafts of Q1
  compared vendors against the perception reference as if it were
  the gate; the pre-registered gate is 100 ms tighter than the
  perception reference for reasons documented in gates.yaml
  rationale, and ElevenLabs — the "winner on latency" — fails
  the pre-registered gate in every session

**What this does NOT change**:
- **Vendor ranking on TTFA is stable**: ElevenLabs consistently
  faster than the rest (see F-11); Deepgram / Cartesia consistently
  slower than ElevenLabs but faster than OpenAI in the one session
  they were measured
- Q1's real-time-voice guidance now reads "no measured vendor
  cleared the pre-registered 400 ms gate; ElevenLabs got closest
  at 469 ms but that held only for the first two sessions and
  moved to 816 ms in S3, so it also fails the softer 500 ms
  perception-reference bar under session-to-session variance"

**Prior drafts erroneously reported Deepgram at ~180 ms p50 /
~230 ms p90**. That figure is not supported by any measurement
in `analysis/latency-*/latency.json`; every latency-mode Deepgram
row shows p50 = 564-583 ms, p90 = 670-674 ms. See the retraction
in [footnote ³](#footnote-3-deepgram-conversational-ttfa) above.

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
(band counts + failure incidence per provider/use-case) and
[`analysis/campaign-20260809T204608Z/acceptance.json`](../analysis/campaign-20260809T204608Z/acceptance.json)
(hygiene gates: 1200 files, 1200 pass — the hygiene rules
discriminate; the WER rule does not).

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
| T5 | Latency 736/956 ms (2× next; original observation from campaign-cached row) | OpenAI | **Confirmed (slower than ElevenLabs)** — S3 = 1369/1882 ms, all 3 sessions consistently slower than ElevenLabs. Stability sub-finding refuted (see F-11). | [T5](../analysis/verification/T5_openai_latency.md) |
| T6 | Audiobox #1 both UC | Speechify | **Confirmed with reversal** — alt voice edmund_32 scores *higher* than pinned voices; still #1 of 9 | [T6](../analysis/verification/T6_speechify_voice_bias.md) |
| T7 | Fastest TTFA (439/479 ms in S1; original observation) | ElevenLabs | **Confirmed faster than OpenAI**, all 3 sessions. But **NOT stable** — S3 = 694/816 ms (+58%/+70% vs S1). The prior "sub-500 ms p90 reliably" recommendation is retracted; see F-11. | [T7](../analysis/verification/T7_elevenlabs_ttfa.md) |
| T8 | Cheapest $0.030/1K | Orpheus | **Refuted with a bigger finding** — 14.59s hard output cap; cost is fixed-per-call not linear-with-text | [T8](../analysis/verification/T8_orpheus_cost.md) |
| N1 | Audiobox #8/#8 vs DNSMOS #1/#1/#2 narr | OpenAI | Pending (manual listen) | [N1](../analysis/verification/N1_openai_narration_inversion.md) |
| N2 | DNSMOS OVRL+SIG #8/#8 conv | Fish | **Confirmed** — Fish noise floor +12.6 dB above 8-vendor median (2× threshold); 3rd independent pipeline agrees | [N2](../analysis/verification/N2_fish_conv_dnsmos.md) |

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
~$0.02) that refuted the T7 stability sub-finding — see
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11-retraction-of-the-latency-stability-is-a-distinct-axis-finding).

---

## Decision framework (three questions)

Answer these in order. Only proceed once the previous question has
a clear answer for your use case.

### Q1 — Hard constraints

- **Any turn ≥ 15s?** Orpheus is out (14.59s output cap).
- **Any downstream ASR / MOS / resample pipeline?** Cartesia needs a
  −1 dBFS peak-limiter first, or accept ~46% loss to DNSMOS refusals.
- **Real-time-voice latency ceiling?** Two thresholds to keep
  straight: the **pre-registered gate is `ttfa_p90_ms < 400`**
  (`configs/gates.yaml`, chosen as headroom below the 500-600 ms
  perception threshold), and the **perception-threshold reference
  from the literature is ~500 ms** (spec A.1).
  - Against the pre-registered 400 ms gate: **no measured vendor
    passes.** ElevenLabs Flash's best measurement was 469 ms p90
    (S2); Cartesia 529 ms; Deepgram 670 ms; OpenAI 946 ms. Every
    measured streaming vendor fails the pre-committed gate in
    every session it was measured. See [TTFA-gate admission](#ttfa-gate-admission).
  - Against the softer 500 ms perception reference: ElevenLabs
    Flash cleared it in S1 (479 p90) and S2 (469 p90), then
    failed it in S3 (816 p90). The prior "reliably under 500 ms"
    recommendation is retracted; see F-11.
  - **Speechify / Fish / Google / Orpheus** are unmeasured on
    streaming TTFA (their adapters don't stream); they may or
    may not meet either bar — *unknown*, not *disqualified*.
  - **Prior drafts erroneously called out Deepgram as a "well
    below 500 ms" alternative**. That claim (based on an
    unsupported ~180 / ~230 ms figure) is retracted; actual
    Deepgram p50 / p90 was 583 / 674 ms in the S1a session,
    564 / 670 ms in S1b — Deepgram fails both thresholds.
  - For a real-time deployment: **measure from your own
    environment across ≥5 sessions** with client-side event-loop
    lag logged (F-11), and expect 50-90% session-to-session
    variance from residential clients. Do not provision from any
    of the numbers above as a ceiling.
- **Byte-identical caching?** Impossible with any of the 8; save the
  audio yourself.

### Q2 — Which "quality" matches your users?

- **Warm / engaging** (consumer storytelling, audiobook, brand voice) →
  **Speechify** wins Audiobox on both use cases with 3.7–7.3σ
  significance (recomputed with per-comparison SE, no threshold
  heuristic; honest #2 for narration PQ is Cartesia — Orpheus's
  9.5σ was a truncation-cap artifact and is excluded, see the
  Rankings summary above). On cost, Speechify ($0.10 / 1K words at 100K/mo) is the
  **cheapest among the top-2 warm-quality vendors** — ElevenLabs at
  $0.22 is the #2 warm vendor and 2.2× more. Absolute cheapest
  overall is Orpheus at $0.030, but Orpheus is bottom-2 on Audiobox
  PQ conv and disqualified from narration by its 14.59-second output
  cap.
- **Clean / pristine** (enterprise IVR, accessibility, transactional
  voice) → **OpenAI** ties for #1 on DNSMOS OVRL on both use cases
  (0.7–1.3σ vs the tied competitor, not significant — no vendor
  cleanly "wins" this axis at n=75). **OpenAI ($0.075 / 1K words) is
  34% of ElevenLabs' price ($0.22, tied competitor on conv) and 50%
  of Deepgram's ($0.15, tied competitor on narration)** — so a
  50-66% saving depending on which tied competitor you compare
  against. See the Rankings summary above for the per-comparison
  SE(diff) figures.

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

The rewrite of the SE methodology is in the Rankings summary above.
Prior versions of this doc used a heuristic 0.05 threshold — that's
been replaced with the per-comparison SE(diff) test.

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
  (0–10). Trained on aesthetic ratings; rewards *warmth,
  expressiveness, engagement*.
- **AB.CE** — Meta Audiobox Aesthetics *content_enjoyment* axis (0–10).
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

# --- Latency: all three sessions (S1 + S2 + S3) ---
# S1 (2026-08-09) — first pass, 50 trials × 4 streaming vendors
uv run veval analyze latency-20260809T214106Z --stages latency
uv run veval analyze latency-20260809T222356Z --stages latency
# S2 (2026-08-11) — second pass, adds T5/T7 verification
uv run veval analyze latency-20260811T183028Z --stages latency
uv run veval analyze latency-20260811T183202Z --stages latency
# S3 (2026-08-12) — third pass with concurrent ping baseline; the
# session that refuted the "ElevenLabs stability" claim (F-11).
# The concurrent ping-baseline log is committed at
# `analysis/ping-baseline-20260812T191138Z.jsonl` (274 probes to
# Cloudflare 1.1.1.1); the audio runs/ are regenerable per 03.
uv run veval analyze latency-20260812T191143Z --stages latency  # OpenAI, 50/50
uv run veval analyze latency-20260812T191323Z --stages latency  # ElevenLabs, 40/50 (spend-cap)

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
