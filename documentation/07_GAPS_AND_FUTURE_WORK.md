# 07 · Gaps and future work

*What v1 didn't cover, why, and what a v2 pass would add.*

> **⚠ Scope disclaimer** · Findings as of 2026-09-01 on specific
> vendor accounts (paid public tiers) and one voice per vendor per
> use case (plus a five-vendor alt-voice comparison from the Phase 2
> experiment pack, see gap #2 below). No financial relationship with
> any vendor. Full scope in [../DISCLAIMER.md](../DISCLAIMER.md).

> **Two-phase context** · Phase 1 (baseline campaigns, 2026-08-09 to
> 2026-08-31) established the gaps and threats catalogued below.
> Phase 2 (targeted experiment pack, 2026-09-01) partially closed
> three of them — alt-voice sweep, cross-vendor drift generalisation,
> and latency session-count. Each item below flags where Phase 2
> narrowed the gap and where the residual v2 workstream still
> stands. Full receipts:
> [EXPERIMENTS_2026-09-01.md](EXPERIMENTS_2026-09-01.md).

---

## Structural gaps (cannot fully mitigate in v1 scope)

These are limits inherent to a single-person, three-week, ~$13
project. Each is documented as an explicit v2 workstream rather
than glossed over.

### 1. No human perceptual validation (n=1 rater is not enough)

The operative pre-registered target for this campaign was
**216 judgments** per
[`DEVIATIONS.md` D-009](../DEVIATIONS.md#d-009) (`prereg-v1.7`,
2026-08-08) — 36 pairs across 9 systems × 2 use cases × 3 reps
— with clustered bootstrap 95% CIs. Under D-009 the target
IS the spec's 3-rep minimum floor for the 9-system roster (not
"above" a live 126 floor — 126 is 3 reps × 21 pairs × 2 UC on
the pre-D-003 7-system spec, which D-009 superseded). At n=1 self-rater,
those CIs would be **conditional on the single rater** — a different
rater could produce non-overlapping "95% CIs" on opposite
preferences, both statistically valid, both worthless as
human-preference evidence.

Executing the ceremony and disclaiming the result would be a shape of
over-claim this project refuses to make. See
[06_KEY_FINDINGS.md § D-H](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2)
for the full rationale.

**v2 workstream**: recruit 15–30 blinded raters, run the
`veval rate {build,normalize,serve,fit}` pipeline (implemented
in [`src/veval/human/`](../src/veval/human/) — `pair_builder.py`,
`loudness.py`, `bt.py`; one missing piece is a `veval invites`
tokened-URL builder that was described in the spec but never
written), compare rankings to the two machine-pipeline rankings,
publish which pipeline aligns better with human perception on
which use case.

### 2. One voice per vendor per use case (partially closed by Phase 2)

Each vendor was tested with one representative voice per use case,
locked in `configs/voices.yaml` before results existed. Voice
choice within a vendor produces statistically significant AB.PQ
shifts on the paired-per-item test — measured for Speechify in
T6 (20 items per use case × 5 strata × 4 items each), where the
alt voice `edmund_32` scored **+6.05σ AB.PQ over the pinned
`geffen_32` on conversational** (cross-gender: female → male) and
**+4.02σ AB.PQ over the pinned `wyatt_32` on narration**
(same-gender: male → male; T6 verdict says of the narration pair
"same gender (both male)"). Note PQ is the technical-cleanliness
Audiobox axis (agrees
with DNSMOS at ρ = +0.24 mean — see
[06 § F-8](06_KEY_FINDINGS.md#f-8)), not the aesthetic axis. The
T6 narration same-gender result is the load-bearing observation
that voice-choice shifts survive gender matching on at least one
vendor.

**Phase 2 partial close** (2026-09-01, Follow-up 4): extended the
voice-swap test from Speechify only in v1 to Speechify + OpenAI +
Fish + Deepgram + Google. Under the paired per-item test, every
alt voice tested produced a statistically significant AB.PQ shift
(3.28σ–13.46σ across the 4 Follow-up-4 vendors, all under
cross-gender confound; +4.02σ same-gender on Speechify T6
narration). See [F-7](06_KEY_FINDINGS.md#f-7) for the full
paired-z table + gender-decomposition discussion.

**Residual v2 workstream**: (a) run **same-gender** alt-voice
sweep across the 7 non-Speechify vendors (2 voices per vendor,
same gender as pinned, 20-item pilot each; ~$1–2 total) to
extend T6's same-gender +4.02σ observation from 1 vendor to 8;
(b) run 3–5 additional alt voices per vendor per use case to
answer whether vendor rankings survive across the full voice
space, and where vendor tag-taxonomy (warm / bright / dynamic /
etc.) reliably predicts aesthetic score.

**Related asymmetric-scrutiny gaps**:

- **Orpheus CONV truncation carries no footnote.** Orpheus's
  conversational column is truncated 25/75 files against the same
  14.59-s cap that gets footnoted for its narration column (see
  04 § footnote ¹). The conv per-vendor table has no equivalent
  footnote; a symmetric-scrutiny fix is one paragraph and a copy
  of the AB.PQ per-stratum analysis done for narration. Not fixed
  in v1.
- Cartesia's loser-side outlier (clipping) got two targeted
  verification pathways (F-4a's independent-pipeline corroboration +
  T1's regen plan). Speechify's winner-side outlier (Audiobox #1 on
  both use cases) got one weak test (T6, n=2 voices in same vendor).
An equivalent adversarial hypothesis for Speechify would be: **"Does
Audiobox systematically reward Simba-3.2's mastering signature
(EQ / compression profile) rather than anything a listener would
call quality?"** — motivated by F-8's "MOS predictors reward
different acoustic constructs" thesis. Testing this would need
either (a) a controlled EQ / compression pass on other vendors'
audio to see if Audiobox scores follow the mastering rather than
the voice, or (b) the v2 human-rater panel from D-H. v1 did neither.
T6's "confirmed with reversal" should be read as **n=2 evidence
that voice choice within Simba-3.2 doesn't sink the ranking**, not
as evidence that Audiobox's ranking of Speechify #1 reflects
generalisable listener preference.

### 3. Corpus authored by the evaluator (60 of 75 per use case)

**60 of the 75 items per use case were authored to a documented
brief** (support-agent turn distribution + long-form narrative
structure); **the remaining 15 are the pre-registered
contamination probe** — Harvard sentences (conversational) and
public-domain literary openings (narration) per spec § 3.3 (see
[02 § Contamination probe](02_METHODOLOGY.md#probe) for the
per-stratum WER data + probe-excluded bands). Corpus is
committed to git; another evaluator can reproduce with different
content. **The finding that provider strengths cluster
orthogonally on this corpus is not necessarily portable to a
very different corpus** (e.g., poetry, technical documentation,
dialog with heavy dialect). The probe items are the only ones
whose licence is inherited (public-domain source text); the 60
authored items are CC BY 4.0 per [`LICENSE`](../LICENSE).

**v2 workstream**: repeat the campaign against 2–3 additional
corpora sampled from public sources (LibriSpeech test-clean for
narration; SIP-audio traces for conversational). Test whether
rankings survive the corpus change.

### 4. English only

Vendors' multilingual claims are untested here. Several vendors
advertise multi-language voices as differentiators; we can neither
confirm nor refute those claims.

**v2 workstream**: repeat the campaign on Spanish + Mandarin + one
low-resource language (e.g., Swahili) using the same methodology.

### 5. Client-side latency measured from a residential Windows 11 environment (session count improved by Phase 2)

Absolute TTFA / RTF numbers are one point in a session-to-session
distribution measured from residential Windows 11 (see F-11);
they are not upper bounds on what an enterprise-cloud-VM
deployment would see, in either direction. Provider *rankings* on
latency are portable; absolute *values* are session-to-session
observations (F-11), not ceilings. See
[06_KEY_FINDINGS.md § D-G](06_KEY_FINDINGS.md#d-g-enterprise-portability).

**Phase 2 partial close** (2026-09-01, Follow-up 3): added Sessions
4 and 5 to the F-11 latency series, bringing total to 6 sessions
across 4 dates. Confirmed S3 was a transient outlier and rankings
(ElevenLabs faster than OpenAI) hold in every session; range on
ElevenLabs p90 is now 461-816 ms (+77%), OpenAI 946-1,882 ms (+99%).
Six sessions cleared the ≥5-session **count** Phase 1 called out,
but Phase 1 also called for **client-side event-loop lag logging**
as a control on each session — that lag logging was not run on
any of the 6 sessions, so mechanism attribution ("wide-tail
vendor" vs "client-side contamination") remains unattributed
even at n=6 for the client-side residential-Windows venue. This
gap is partially closed at count, still open at controls.

**Residual v2 workstream**: re-measure TTFA/RTF from AWS + GCP VMs
colocated with each vendor's serving region. Publish an
enterprise-cloud-VM baseline alongside the residential baseline,
both characterised across ≥5 sessions per venue.

### 6. Subscription-tier serving priority may differ from enterprise contracts

Measurements were taken on paid public tiers: Speechify Starter
$10/mo, ElevenLabs Creator, Cartesia Pro $5/mo, Deepgram $200 signup
credit, OpenAI Tier 1, Replicate pay-per-use, Google Cloud pay-per-use,
Fish Audio paid. Enterprise SLAs and volume-negotiated contracts
may produce materially different behavior on rate limits, latency
SLAs, cost per unit, and model access.

**v2 workstream**: partner with a mid-market buyer's actual
enterprise deployment (with permission), replay the corpus, compare
rankings across tier boundaries.

### 7. CPU-only analyzer execution

No validity impact on scores (deterministic transforms of audio
bytes) or rankings. Only affects wall-clock cost for reproducers.
GPU reproducers should observe identical scores at 5-10× the speed.
Documented in [`configs/hardware.yaml`](../configs/hardware.yaml).

**v2 workstream**: (optional) publish a GPU wall-clock benchmark
against the CPU baseline as a reproducibility receipt.

### 8. Pareto-frontier build + Bootstrap-CI domination not executed in v1

The pre-registered scoring model in
[02 § 5](02_METHODOLOGY.md#5-pre-committed-hard-gates--tie-band-ranking-not-a-weighted-composite)
has four components: hard gates (executed and adjudicated —
see [04 § Pre-registered gate outcomes](04_RESULTS.md#pre-registered-gate-outcomes)),
gate-robustness sweep (executed — receipt at
`analysis/campaign-20260831T175358Z/score.json`, discussed in
04's [Pre-registered gate outcomes](04_RESULTS.md#pre-registered-gate-outcomes)),
Pareto frontiers on the remaining axes (not executed), and
Bootstrap 95% CIs on frontier positions (not executed). Only the
last two are gapped, and both are blocked by the same upstream
decision — D-H's deferral of the BT panel — not by the scoring
package as a whole:
[`src/veval/score/gates.py`](../src/veval/score/gates.py) and
[`src/veval/score/robustness.py`](../src/veval/score/robustness.py)
have no BTFit dependency at all and ran without one;
[`src/veval/score/correlations.py`](../src/veval/score/correlations.py)
also has no BTFit dependency, but the receipt's `correlations`
block is `[]` in this pass. The reason it is empty is not
inability to compute — the module runs on per-item quality
signals from `quality.json` and would produce output — but
duplication: F-8's cross-pipeline Spearman ρ was already
committed under
[`src/veval/analyze/cross_metric.py`](../src/veval/analyze/cross_metric.py)
before `veval score` was wired up, so the score-side helper was
left un-called to avoid publishing two competing ρ tables under
different paths. cross_metric.json is the source of truth for
the F-8 numbers; the score/correlations.py path is a v2
consolidation task, not a gap in the evidence. Only
[`src/veval/score/frontier.py`](../src/veval/score/frontier.py) has
the D-H dependency:
`build_frontier(bt_fit: BTFit, ...)` signature at line 95
consumes BT strengths + their bootstrap CIs, and the
CI-domination check at lines 124-125 reads
`bt_fit.strength_ci_lower` / `strength_ci_upper` directly.
Without a fitted BTFit there is nothing to feed the frontier
build, and therefore nothing to bootstrap over. There is an
admin page at
[`src/veval/admin/pages/5_Frontier.py`](../src/veval/admin/pages/5_Frontier.py)
that reads the `frontiers` block inside
`analysis/score.json`. The score.json file exists in v1
(gates + sweep populated it), but the `frontiers` block is `{}`
because there is no BTFit input, so the page has nothing to
plot until D-H closes.

The v1 substitute is per-axis unpaired SE(diff) tie bands in
[04's Rankings summary](04_RESULTS.md#rankings-summary). This
carries the same "no domination without evidence" spirit as the
missing Pareto adjudication but does not produce an explicit
frontier-membership claim, does not run bootstrap on differences
of BT scores, and does not attach CIs to a 2-D (quality × cost)
or (quality × latency) point.

**v2 workstream**: the direct fix is running the D-H BT panel,
which unblocks a small glue call from `veval rate fit`'s BTFit
into `frontier.py` and produces `analysis/score.json` for the
full 8-vendor dataset. A lighter-weight interim on the same code
is not straightforward — `build_frontier` accepts only BTFit, so
producing a frontier from per-vendor mean quality signals would
either need a new signature that consumes plain per-vendor means
(a code change, not just re-running the existing module) or a
BTFit-shaped adaptor over the 3-draw variance subset (whose 10
items × 3 draws are not commensurate with the 75-item campaign
rankings the docs report). Neither is a drop-in run of the
existing module, and the honest read is that closing this gap
requires either the BT panel or a small piece of new code — the
CLI + admin page are ready for the output either way.

### 9. `configs/analyzers.yaml` carries eight TODO placeholders — three drive published numbers, one is a post-hoc-recorded near-miss, two are moot, two are the pre-registered power calc

Full inventory:

| line | field | status | drives what |
|---:|---|---|---|
| 96 | `audiobox_revision: TODO_pin_sha_before_campaign` | **live, unpinned** | AB.PQ + AB.CE (every quality claim) |
| 179 | wav2vec2 `revision: TODO_pin_sha_before_campaign` | **live, unpinned** | two-judge agreement WER |
| 183 | faster-whisper `revision: TODO_pin_sha_before_campaign` | **live, unpinned** | two-judge agreement WER |
| 191 | `wer_normaliser_hash: TODO_compute_hash_when_module_lands` | **live in config**; `wer.py` computes the SHA (`75379ec8…`) at runtime and writes it into `analysis/campaign-*/wer.json` — a **post-hoc-recorded** value, not a pre-registered one | which jiwer normaliser was resolved |
| 34 | TTSDS2 `dataset_id: conversational` (Phase-B TODO) | **moot** — TTSDS2 skipped per [D-A](06_KEY_FINDINGS.md#d-a) | (nothing on this dataset) |
| 46 | TTSDS2 `dataset_id: default` (Phase-B TODO) | **moot** — same as above | (nothing) |
| 207-208 | `n_judgments_target: 210` / `n_judgments_minimum: 126` | **not TODO, but pre-D-009 stale** — the campaign's operative target was raised to 216 in [`D-009`](../DEVIATIONS.md#d-009) (`prereg-v1.7`, 2026-08-08) after D-003 grew the roster to 9 systems and reps compressed 5→3; under D-009 target and floor collapse to the same 216 for the 9-system roster (216 = 3 reps × 36 pairs × 2 UC IS the 3-rep floor), and D-009 § "Where to look" specifically says the `mdd` block should re-run at n=216, which never happened | what number to compare MDD against — target and floor both 216 under D-009 |
| 211 | `mdd_at_target: null   # TODO(Phase-D)` | **live, null** — never filled in | the minimum-detectable-difference the BT panel was designed to catch at the operative-post-D-009 target of 216 judgments |
| 212 | `mdd_at_minimum: null  # TODO(Phase-D)` | **live, null** — never filled in | since D-009 collapsed target and floor to the same 216, this rung is either redundant with `mdd_at_target` or, if a genuine lower rung is wanted, would need a smaller rep count (never specified post-D-009) |

Three separate gaps live inside one file:

**(a) Three neural-model revisions unpinned (lines 96, 179, 183)**.
Those placeholders propagated into `analysis/campaign-*/wer.json`
`judges[*].revision` byte-identical across R2 and R3.
`audiobox_revision` governs AB.PQ + AB.CE; the two judge
revisions govern the two-judge agreement WER. Vendor models are
pinned in `configs/voices.yaml` (SHA where the vendor exposes
one — Orpheus per D-005). The pre-registration discipline was
applied everywhere except these three.

**(b) Normaliser hash pinned post-hoc, not pre-registered (line 191)**.
The `75379ec8…` value gap 9 originally cited as a clean
counter-example is computed by `wer.py` and written into
`wer.json` at runtime, not committed in `analyzers.yaml` before
the campaign. That distinguishes what pre-registration buys
(commits *which* normaliser will be used) from what a runtime
hash buys (proves R2 and R3 used the *same* normaliser, whatever
it was). Both wer.jsons carrying the same hash is real evidence
the normaliser did not drift across the R2↔R3 interval — but it
is not pre-registration. Same slip as (a), one seat over.

**(c) MDD re-run was a dated, git-tagged instruction that
never fired — the fourth un-executed pre-registered step (lines 207-212)**.
D-009's own § "Where to look" states: *"the MDD simulation in
`configs/analyzers.yaml`'s `mdd` block re-runs with n=216
before the campaign starts."* It didn't. `mdd_at_target` and
`mdd_at_minimum` were the minimum-detectable-difference values
the BT power analysis was supposed to compute before the
campaign — the numbers that would have said whether n=216 was
adequate. The block pins `mdd.method: "simulated BT with
clustered bootstrap (2,000 resamples)"` in full but the
`n_judgments_*` rungs are pre-D-009 stale (`210 / 126` should
be `216 / 216` — since D-009 compressed reps to the spec
minimum, target and floor are the same number for the 9-system
roster), and both `mdd_at_*` values are `null`. This is the
same shape as three other pre-registered steps that failed to
execute: the Pareto frontier ([gap 8](#8-pareto-frontier-build--bootstrap-ci-domination-not-executed-in-v1)),
the gate-robustness sweep ([04 § Gate-robustness sweep](04_RESULTS.md#gate-robustness-sweep),
executed retroactively in R19), and the three analyzer SHA
pins (gaps a-b above). The MDD re-run completes that set: a
specific, dated, git-tagged instruction to run before results
existed, not carried out. [D-H deferred the BT panel on
rater-count grounds](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2);
the pre-registered MDD power calc that would have said whether
n=216 was enough was also never filled in. The `rationale`
field in the same block already says "Interval-based decision
rules without a stated MDD leave 'powered to detect X'
unstated" — the config called its own shot.

**Why the compound gap matters**: 02 § 1's pre-registration
receipt was sold as covering "corpus, vendors, voices, gates,
analyzer settings, judges, cost model". Four of eight TODO lines
in `analyzers.yaml` are live and unresolved (the three neural
revisions + the normaliser hash), and two more (MDD pair) are
null. A fresh clone today re-downloads the three HF repos at
whatever `main` serves. The R2↔R3 replication (three weeks apart,
same environment, Spearman ρ = 0.905–1.000 across signals) is
evidence the resolved stack was stable across the interval and
does bound the drift risk to that window — but exact-value
reproduction outside it is not guaranteed. Rank-level
reproduction is the load-bearing promise; the exact-numeric
promise is now explicitly qualified in
[03 § Reproduce the published evaluation](03_RUNBOOK.md#reproduce-the-published-evaluation)
+ [README § Provenance](../README.md#provenance) +
[02 § 1 honest exception](02_METHODOLOGY.md#1-pre-registration-with-git-tags).

**v2 fix**: (a) resolve each of the three neural revisions to a
real SHA (HuggingFace commit hash — one API call per repo, three
lines to `analyzers.yaml`); (b) resolve the normaliser hash from
runtime into the config so a fresh clone reads the pre-committed
value + refuses to run if the file's SHA of the normaliser
function no longer matches; (c) re-sync `n_judgments_target` to
216 per D-009 (`prereg-v1.7`) and fill in `mdd_at_target` +
`mdd_at_minimum` from the simulated BT power analysis the
`rationale` field describes (Phase-D workstream that was never
run); (d) tag the amended config as `prereg-v1.11` before any v2
run; (e) upgrade the `veval doctor` check to refuse to proceed
if `analyzers.yaml` contains **any** of: a `TODO_` placeholder
string, a `null` value in a pre-registered numeric field (the
MDD nulls would have passed a string-only check silently), or a
value that a subsequent `DEVIATIONS.md` entry has explicitly
superseded (the `n_judgments_target: 210` line survived several
review rounds of BT-count corrections in prose because no gate
cross-referenced it against D-009's amendment).
Wall-clock cost is minutes for (a)+(b)+(d)+(e), a few hours for
(c) — this gap is a v1 process miss, not a technical constraint.

---

## Gaps addressed in v1

Documented for completeness — these were on the original threats
list and got substantive mitigation during the project:

- **wav2vec2 judge inflates absolute WER** (F-2) — mitigated by
  reporting WER as *relative-ranking-only*, never absolute. The 6-signal
  quality panel gives triangulation for aggregate quality claims.
- **TTSDS2 skipped** (D-A) — mitigated by adding DNSMOS as the second
  MOS pipeline (D-B / D-011); the 6-signal + cross-pipeline agreement
  analysis substitutes for the missing D3 primary.
- **Single-session latency** (D-1) — mitigated by T5 + T7 adding a
  second 50-trial session, then a third session (2026-08-12) with a
  concurrent ping-to-Cloudflare baseline to rule out ISP
  confounding, then extended to a total of **6 sessions across 4
  dates** in Phase 2 (Sessions S4 + S5 on 2026-09-01). Both vendors
  moved 50-90% p50 across the six sessions; the initial "stability
  is a distinct axis" reading was **not supported**. S3 confirmed as
  transient outlier. See
  [06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11). Six sessions
  meets the ≥5 threshold called out in v1; the residual gap (see
  structural gap #5) is now about *venue*, not session count.
- **F-6 loudness-fade generalisation** — Phase 1 reported a
  reproducible fadeout on ElevenLabs item L03 and framed it as an
  item-specific quirk (F-6). Phase 2 Follow-up 1 generalised the
  test to fresh long-form items across 8 vendors and found a
  cross-vendor phenomenon at 6.2% aggregate rate (ElevenLabs 25%,
  Deepgram + Orpheus 12% each, other five 0%). The finding is
  **stochastic across runs** and **mitigable via chunking**. See
  the F-6 rewrite in
  [06_KEY_FINDINGS.md § F-6](06_KEY_FINDINGS.md#f-6).
- **Cartesia clipping: systemic or batch?** (T1 hypothesis) — mitigated
  by F-4a's independent-pipeline corroboration; T1 verdict Confirmed
  before Phase 2c even began.
- **Ranking depends on MOS predictor family choice** (F-8) — mitigated
  by *publishing both matrices* rather than aggregating into a single
  quality score, and naming the specific rank inversions (OpenAI,
  Speechify, Cartesia) as F-8 findings.

---

## Deferred by scope (not attempted in v1)

Explicit "not in this version" list. Each is a valid v2 workstream.

- **No cross-lingual measurement** — English only
- **No accent or style variation per provider** — one voice per vendor
  per use case, locked in configs
- **No streaming-quality measurement** — buffered playback only; on-the-fly
  quality (mid-utterance artefacts, streaming latency variance) not tested
- **No conversation-flow / context effects** — items evaluated in isolation;
  no turn-taking, no context carryover across items
- **No robustness-to-interruption testing** — barge-in and mid-utterance
  correction behavior not exercised
- **No production-load / concurrency behavior at scale** — measured
  1–3 concurrent requests per provider; enterprise 100+ concurrent
  behavior untested
- **No prompt-injection / adversarial-input robustness** — corpus is
  well-formed English; behavior on malformed / adversarial input
  (very long tokens, non-printable characters, prompt-injection strings)
  untested
- **Two cheap tests proposed, not yet run** (each < $0.15,
  < 30 min wall-clock, both flagged in an earlier review round and
  scaffolded in [03 § Reproduce the Phase 2 experiment pack](03_RUNBOOK.md#reproduce-the-phase-2-experiment-pack)):
    - **T10 — Orpheus `max_new_tokens` check.** Distinguishes
      whether the 14.59-s output cap (F-5, T8) is a
      deployment-config default (fixable in one API-flag change) vs
      a model-intrinsic hard cap (requires chunking-engineering).
      README and 05 both currently flag this as untested; running
      T10 would let the PM recommendation collapse from "either / or"
      to a single actionable path.
    - **Sample-rate header sweep.** Confirms no vendor is *still*
      shipping a placeholder sample rate in the WAV header
      (Deepgram's 44,737-s placeholder was fixed by
      `finalize_wav_header()`; the sweep would sanity-check that
      no other vendor has a similar defect). Related to F-1a.
- ~~**No per-vendor RTF (narration throughput)**~~ — **closed in R3.**
  The pre-committed `rtf ≥ 3.0` narration gate is adjudicated on
  [`campaign-20260831T175358Z/latency.json`](../analysis/campaign-20260831T175358Z/latency.json)
  (fresh run, `n_fresh = 75` per vendor per use case,
  `long_stratum_n = 8` per cell). Result: **5 pass / 3 fail** —
  first pre-registered gate in the evaluation with a discriminating
  outcome. Pass: OpenAI, ElevenLabs, Speechify, Google, Cartesia.
  Fail: Deepgram (2.14), Fish (1.70), Orpheus (0.83, slower than
  real-time against the truncated 14.59-s output). Full breakdown
  in [04_RESULTS.md § RTF admission](04_RESULTS.md#rtf-admission).
  Retraction of the earlier "not adjudicated in v1" wording logged
  as [CORRECTIONS row 24](../CORRECTIONS.md).
- **R2 campaign ran fully from content-hash cache — closed for R3
  by the `--no-cache` re-run** — `campaign-20260809T204608Z` (R2)
  is a cache-only replay; every audio file was generated at an
  earlier, unrecorded date, and the manifest records only the
  cache-hit timestamp, not the original synthesis timestamp. Combined
  with F-1 (nothing byte-reproducible), each R2 cell in the
  results tables is a **frozen single draw with an unrecorded
  generation date**. Quality and hygiene claims are unaffected
  (they read audio bytes, not timestamps) but the "measurement
  date on every finding" discipline in 02 degrades at the
  raw-audio-generation level for R2. **Closed for R3**: the
  `--no-cache` primary-campaign re-run
  (`campaign-20260831T175358Z`, R3) ran on 2026-08-31 for
  **$7.85 metered** (cost_model.json total; the earlier
  ~$40 estimate on this bullet was pre-run), populated per-item
  `synthesis_time` for every (vendor, use case) cell
  (`n_fresh = 75`), adjudicated the RTF gate 5 pass / 3 fail
  (see [04 § RTF admission](04_RESULTS.md#rtf-admission)), and
  is the reference measurement for every "gate outcome" claim in
  the docs. The R2 caveat still governs the R2-sourced headline
  tables in [04 § Full per-provider results](04_RESULTS.md#full-per-provider-results)
  (the R2/R3 label + cell-source disclosure is a separate
  reporting gap). Retraction of the earlier "would-cost-$40 +
  gap-open" framing logged as
  [CORRECTIONS row 24](../CORRECTIONS.md).

---

## What a v2 pass would look like

If someone were to fund a proper v2 today, the priority-ordered
workstream list would be:

1. **Multi-rater BT panel** (highest-leverage, answers F-8's
   "which construct maps to human perception?" question) —
   15-30 raters, ~1 week of coordination + $500 for rater
   compensation
2. **Alt-voice sweep per vendor** — 3-5 voices × 8 vendors ×
   20 items = 480 fresh generations, ~$5, ~2 hrs
3. **Enterprise-VM latency baseline** — AWS + GCP colocated
   measurements per vendor's inference region, ~1-3 days of
   VM setup + $50 cloud spend
4. **Cross-lingual pass** — Spanish + Mandarin + 1 low-resource
   language against the same 8 vendors, ~$50-100 depending on
   vendor pricing
5. **Alt-corpus robustness** — 2 additional corpora (LibriSpeech
   + SIP dialogs), same 8 vendors, ~$50
6. **Enterprise-tier partner replay** — 1-2 real enterprise
   deployments (with permission), same corpus, compare to our
   public-tier results
7. **Streaming-quality measurement** — extend the harness to
   analyse on-the-fly audio quality, then replay the campaign

**Estimated v2 total cost**: ~$700-1500 in cloud + rater fees.
**Estimated v2 wall-clock**: ~3-4 weeks of coordinated work.

This project is designed so a v2 can be built additively on the
existing infrastructure — every gap above is a targeted extension
of the existing analyzer chain rather than a rewrite.

---

## Where to go next

- [../DISCLAIMER.md](../DISCLAIMER.md) — full scope + no-affiliation disclosure
- [06_KEY_FINDINGS.md § threats-to-validity](06_KEY_FINDINGS.md#threats-to-validity) —
  same items linked back to the specific decisions that drove them
- [05_CASE_STUDY.md § "What wasn't done and why"](05_CASE_STUDY.md#what-wasnt-done-and-why) —
  the same gaps in narrative form
- [06_KEY_FINDINGS.md § D-H](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2) —
  the specific reasoning for the biggest omission (BT panel)
