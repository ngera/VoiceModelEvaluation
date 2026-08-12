# 04 · Results Summary

*Full per-provider measurements across 8 vendors × 2 use cases,
plus the verification-pack verdicts and the cost calculus a
decision-maker needs.*

> **⚠ Scope disclaimer** · Results as of 2026-08-11 on specific
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

**Important scope note** (item 31 of external review): **each cell in
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

For lower-is-better columns (clip samples, noise floor dBFS, WER %,
TTFA ms, $/1K words) the colour flips direction — **green = lowest = best**.
For `clip samples`, values of 0 are always green (perfect); any value
≥100 is red regardless of ranking. TTFA cells marked "—" indicate
adapters that don't stream (Speechify, Fish, Google, Orpheus per D-008
and adapter-shape).

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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 14.3</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 14.1</td>
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
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 13.7</td>
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
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 13.8</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 15.1</td>
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
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 16.6</td>
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 583</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 16.4</td>
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
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 26.9</td>
<td align="right">—</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0.030</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 13.0</td>
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
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 27.2</td>
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 0.030</td>
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
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 12.4</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 13.0</td>
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
<td align="right"><img src="https://placehold.co/40x18/c8e6c9/c8e6c9.png" alt="best"> 12.8</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 13.5</td>
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
<td align="right"><img src="https://placehold.co/40x18/ffcdd2/ffcdd2.png" alt="worst"> 14.0</td>
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
<td align="right"><img src="https://placehold.co/40x18/fff9c4/fff9c4.png" alt="mid"> 13.3</td>
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

---

## Rankings summary

**Top-2 per quality axis per use case** — the "who's actually
worth paying for?" table. Each pair is judged **significant** iff
`|Δ| > 1.96 × SE(diff)` where `SE(diff) = √(SE_a² + SE_b²)` and
`SE_i = SD(vendor's 75-item column) / √75`. This is the standard
normal-approximation test at α=0.05. Per-vendor per-signal SDs +
SE_mean values are in [`scripts/_noise_floor_recompute.py`](../scripts/_noise_floor_recompute.py)
output; run the script to reproduce.

**Why this method** (fixes items 1-4 of the external review):
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

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | \|Δ\|/SE(diff) | Verdict |
|---|---|---:|---|---:|---:|---:|---|
| Audiobox PQ (warm) | speechify | 8.150 | orpheus¹ | 8.002 | +0.148 | **9.5σ** | **SIG_DIFF** |
| Audiobox CE (warm) | speechify | 6.662 | elevenlabs | 6.466 | +0.197 | **7.3σ** | **SIG_DIFF** |
| DNSMOS OVRL (clean) | openai | 3.463 | orpheus¹ | 3.453 | +0.010 | 0.7σ | **TIE** |
| DNSMOS OVRL (clean, w/o Orpheus) | openai | 3.463 | deepgram² | 3.442 | +0.021 | 1.1σ | **TIE** |
| DNSMOS SIG (clean) | openai | 3.679 | deepgram | 3.677 | +0.002 | 0.2σ | **TIE** |

¹ Orpheus's narration audio is truncated to ~16% of the expected
reading duration by the model's 14.59-second per-call output cap
(see F-9 T8). Its narration DNSMOS means are computed on
structurally incomplete audio — treat any "Orpheus wins narration
X" as an artifact.

² Deepgram is the honest #2 on DNSMOS OVRL narration once Orpheus
is disqualified for the reason above.

**Interpretation:** all four Audiobox comparisons are meaningfully
different — Speechify's warm-rater lead over the #2 vendor is
**3.7σ to 9.5σ significant**, not a heuristic threshold call. All
DNSMOS top-1-vs-top-2 comparisons are ties — OpenAI's DNSMOS
"win" is essentially indistinguishable from ElevenLabs (conv),
Deepgram (narr), and Orpheus (narr, ignoring the disqualification).

---

## Cross-pipeline agreement (F-8)

Two independent MOS pipelines rank the 8 vendors **differently**.
Cross-pipeline mean Spearman ρ across the 8 vendors:

| Use case | Cross-pipeline mean ρ | Point-estimate reading | 95% CI (Fisher-transformed, n=8) |
|---|---:|---|---|
| Conversational | **−0.13** | Essentially uncorrelated | roughly [−0.75, +0.60] |
| Narration | **−0.27** | Weakly inverse | roughly [−0.81, +0.51] |

**Statistical caveat** (item 9 of external review, spelled out):
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

| Vendor | $/1K @ 10K/mo | $/1K @ 100K/mo | $/1K @ 1M/mo | Notes |
|---|---:|---:|---:|---|
| orpheus | 0.030 | 0.030 | 0.030 | Replicate pay-per-use. **Effective long-form cost ~$0.015/1K chars** (T8: 14.59s cap × ~5 calls per 1K chars × $0.003/call). Prior 04 note said "$0.18-0.60" — that was a decimal-place error, corrected here. |
| **openai** | 0.075 | **0.075** | **0.075** | tts-1-hd (narration) + gpt-4o-mini-tts (conv) |
| fish | 0.075 | 0.075 | 0.075 | s2.1-pro (paid); split-model design (quality vs latency) |
| **speechify** | 0.100 | **0.100** | **0.040** | Starter $10/mo covers 100K; scales well at 1M+ |
| deepgram | 0.150 | 0.150 | 0.150 | Aura-2; $200 signup credit covers early volume |
| google | 0.150 | 0.150 | 0.150 | Chirp3-HD |
| cartesia | 0.500 | 0.160 | 0.196 | Pro $5/mo = 100K credits, then per-1M rate |
| **elevenlabs** | **2.200** | **0.220** | 0.244 | Creator $22/mo = 121K credits; expensive at low volume |

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

## Latency (3 sessions × 4 days, with concurrent ping baseline)

Time-to-first-audio-frame (TTFA), 50 serial trials per session,
conversational S01 corpus item. Three independent sessions across
2026-08-09, -11, -12. **Session 3 was run with a concurrent
ping-to-1.1.1.1 baseline** (274 probes during the S3 window) to
separate vendor variability from local ISP jitter.

| Vendor | S1 p50 / p90 | S2 p50 / p90 | S3 p50 / p90 | Range across 3 sessions |
|---|---|---|---|---|
| **elevenlabs** (Flash v2.5) | 439 / 479 | 424 / 469 | **694 / 816** | p50: 424–694 ms (+64% max shift) |
| openai (tts-1-hd) | 736 / 956 | 936 / 1493 | **1369 / 1882** | p50: 736–1369 ms (+86% max shift) |
| deepgram | ~180 / ~230 (S1 only) | not re-measured | — | — |
| cartesia | 467 / — (S1 only) | not re-measured | — | — |
| speechify · fish · google · orpheus | not applicable* | | | |

*"Not applicable" here means the adapter doesn't stream (Speechify
JSON envelope per D-008; Fish's paid model split; Google's
non-streaming; Orpheus's hosted-inference-poll pattern on Replicate).
TTFA is `total_ms` for these, not the streaming TTFA the other
providers report. See [../DEVIATIONS.md](../DEVIATIONS.md#d-008).

**Concurrent ping baseline during S3** (Cloudflare 1.1.1.1,
274 probes, 500 ms interval): p50 = 8 ms, p90 = 12 ms, min = 5 ms,
max = **29 ms**, stdev = 3.2 ms, 0 errors. **The local ISP was
clean during S3** — the observed vendor-side slowdown is not
last-mile jitter.

**Portable finding** (revised — see F-11 for the retraction of the
prior "stability" claim):

- **Vendor ranking on TTFA is stable**: ElevenLabs is consistently
  faster than OpenAI in every session (429/439/694 vs 736/936/1369
  on p50). The ordering is portable.
- **Absolute TTFA is NOT stable** for either vendor. Both moved
  50-90% p50 session-to-session on our public-tier accounts.
  Neither vendor is "stable" in an operational sense; the initial
  ElevenLabs "sub-500 ms p90 reliably" finding held only in the
  first two sessions and was refuted by S3.
- **The observed vendor variability is not our ISP** — the ping
  baseline confirms this for S3. Candidate causes (untested):
  vendor-side capacity load, time-of-day serving effects,
  local-machine contention on the client (not network).

See [documentation/figures/f3_latency_stability.png](figures/f3_latency_stability.png)
for the visual (pre-S3 — the figure predates F-11 and will be
regenerated in a future pass). Full retraction narrative in
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11-retraction-of-the-latency-stability-is-a-distinct-axis-finding).
Verdict details in
[analysis/verification/T5](../analysis/verification/T5_openai_latency.md)
and [T7](../analysis/verification/T7_elevenlabs_ttfa.md) (both
updated with S3 data).

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
| T5 | Latency 762/946 ms (2× next) | OpenAI | **Confirmed (slower than ElevenLabs)** — S3 = 1369/1882 ms, all 3 sessions consistently slower than ElevenLabs. Stability sub-finding refuted (see F-11). | [T5](../analysis/verification/T5_openai_latency.md) |
| T6 | Audiobox #1 both UC | Speechify | **Confirmed with reversal** — alt voice edmund_32 scores *higher* than pinned voices; still #1 of 9 | [T6](../analysis/verification/T6_speechify_voice_bias.md) |
| T7 | Fastest TTFA (440/474 ms) | ElevenLabs | **Confirmed faster than OpenAI**, all 3 sessions. But **NOT stable** — S3 = 694/816 ms (+58%/+70% vs S1). The prior "sub-500 ms p90 reliably" recommendation is retracted; see F-11. | [T7](../analysis/verification/T7_elevenlabs_ttfa.md) |
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
- **Sub-500 ms TTFA p90 required for real-time voice?** ElevenLabs
  Flash and Deepgram were the only measured vendors clearing this in
  S1-S2 sessions, but **ElevenLabs Flash's S3 measurement (694/816 ms)
  refutes any "reliably under 500 ms" claim** (see F-11). Deepgram
  measured well below 500 ms in S1 only, not re-measured. For a
  real-time deployment, do not provision from these numbers —
  measure from your own environment across ≥3 sessions and expect
  50-90% session-to-session variance. **Speechify / Fish / Google /
  Orpheus** are unmeasured on TTFA (their adapters don't stream);
  they may or may not meet a 500 ms bar — this is *unknown*, not
  *disqualified*.
- **Byte-identical caching?** Impossible with any of the 8; save the
  audio yourself.

### Q2 — Which "quality" matches your users?

- **Warm / engaging** (consumer storytelling, audiobook, brand voice) →
  **Speechify** wins Audiobox on both use cases with 3.7–9.5σ
  significance (recomputed with per-comparison SE, no threshold
  heuristic). On cost, Speechify ($0.10 / 1K words at 100K/mo) is the
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

- Under **1.96σ** → statistically tied at α=0.05; the cheaper vendor
  is the right pick on this axis.
- **2σ to 4σ** → real but modest gap; worth pricing against your
  quality-vs-cost trade-off.
- **Over 4σ** → a real quality gap; only skip the winner if cost
  differential is severe.

The rewrite of the SE methodology is in the Rankings summary above.
Prior versions of this doc used a heuristic 0.05 threshold — that's
been replaced with the per-comparison SE(diff) test.

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
- **WER %** — Mean word-error-rate on items with judge agreement
  (two-judge design: wav2vec2 + faster-whisper). Reported as
  relative ranking only; absolute inflated by wav2vec2's LibriSpeech
  training distribution.
- **TTFA p50 (ms)** — Time-to-first-audio-frame, 50th percentile,
  50-trial session, S01 corpus. **Residential Windows 11
  measurement — absolute values are upper bounds.**
- **$/1K words** — Cost per 1,000 words at the specified monthly
  volume tier (see full cost table).

Full measurement methodology in
[02_METHODOLOGY.md](02_METHODOLOGY.md).

---

## Reproducing these numbers

```powershell
# From the immutable run stores (regenerable)
uv run veval analyze campaign-20260809T204608Z --stages all
uv run veval analyze latency-20260809T214106Z --stages latency
uv run veval analyze latency-20260811T183028Z --stages latency
uv run veval analyze latency-20260811T183202Z --stages latency

# Cross-metric analysis
uv run veval analyze campaign-20260809T204608Z --stages cross_metric

# Regenerate the figures
uv run python scripts/generate_figures.py
```

See [03_RUNBOOK.md](03_RUNBOOK.md) for full install + reproduce
instructions.
