---
title: Defect register — document review rounds
date: 2026-08-06
scope: Defects found and fixed in the v2 document set (spec, implementation plan, research report, architecture diagram) between first draft and current state
status: All listed defects fixed. Open items are listed separately in §5.
---

# Defect register

Three verification rounds were run over the v2 document set before any of it was acted on.
**Every defect below was in a draft produced during this revision cycle — none were in the
original project documents**, which were red-teamed separately and whose findings are
recorded in `EXTERNAL_REVIEW_2026-08-06.md`.

Round 1 covered the spec, implementation plan and diagram. Round 2 covered the research
report. Round 3 was a full re-review of all four documents by four independent passes:
cross-document consistency, report-internal review, spec-and-plan executability, and an
external fact-check with live verification.

**Totals: 17 + 17 + 45 = 79 defects fixed.**

---

## 1. Round 1 — spec, implementation plan, diagram (17)

| # | Defect | Fix |
|---|---|---|
| 1.1 | The illustrative results table violated its own confidence-interval rule — one provider with an overlapping interval was labelled "On frontier" without qualification — and the Rank column had no sort key once the weighted composite was killed | Table re-sorted, statuses corrected, and a note added showing how the rule reclassifies rows |
| 1.2 | Spec and plan gave opposite orderings for pre-registration: the spec settled the split-half check and gate thresholds "before `prereg-v1` is tagged", the plan tagged first and validated on the pilot | Plan's ordering adopted; `prereg-v1.1` amendment path documented |
| 1.3 | The split-half acceptance criterion was circular — it triggered on divergence "beyond the noise floor", which is not computed until after the campaign | Replaced with a pre-committed absolute threshold, with the circularity explained |
| 1.4 | Cost modelling (D6) had no implementation home — no config, no module, no timeline slot — despite cost being a frontier axis | `configs/pricing.yaml` + `analyze/cost.py`, added to the timeline and Phase G |
| 1.5 | Budget line items summed to $34–44 against a stated "$32–48", and the GPU contingency was unbudgeted | Itemised, contingencies made explicit, spend rule pre-committed |
| 1.6 | Variance subset mis-costed by an order of magnitude: "~20K characters" for what is ~200K, and one provider's hosting cost ignored | Corrected (and corrected again in round 3 — see 3.6) |
| 1.7 | "Eight of the eleven changes cost compute" — the list that followed named five, and only five qualified | Corrected to five with the remainder categorised |
| 1.8 | Corpus strata were referenced by three mechanisms but never defined; inherited ratios would have yielded ~3 long items for a gate that needs them | Composition table added; long stratum raised to 8 per use case as a logged deviation |
| 1.9 | Per-provider measurement constraints were dropped — including that one provider's streaming path forces a different latency protocol, which changes what its number means | Restored as a constraints table |
| 1.10 | Proposed CLAUDE.md amendments missed rows that v2 contradicts: dev environment, CLI surface, meta-rule 2's source-of-truth list, stale status and budget | All added |
| 1.11 | "Build the eight boxes" listed nine | Corrected (and again in round 3 — see 3.41) |
| 1.12 | The architecture diagram omitted the admin panel, treated everywhere else as a co-equal front door | FRONT node added |
| 1.13 | Hygiene gates lost their numeric thresholds — "no audible artifacts" is not pre-registrable | −60/−40 dBFS restored; gate made numeric |
| 1.14 | One third of the TTSDS2 finding's fix was missing: the benchmark's documented minimum sample size was never checked | Added (and resolved in round 3 — see 3.7) |
| 1.15 | Corpus volume exceeded the paid tiers the budget books | Overage path added (and withdrawn in round 3 — see 3.15) |
| 1.16 | Analyzer load stated as "~1,000 files" against an actual ~1,300; pairwise session count inherited from a different judgment total | Both corrected |
| 1.17 | The cold read was dropped, leaving the first definition-of-done item unverifiable by anyone | Restored to week 3 and cited from the checklist |

## 2. Round 2 — research report (17)

| # | Defect | Fix |
|---|---|---|
| 2.1 | **A fabricated outcome.** The contributions list claimed a "demonstrated re-run after four weeks quantifying provider drift" — nothing had run | Rewritten as scheduled, not demonstrated |
| 2.2 | Variance count contradicted the spec, and the noise-floor table had no slot for the reduced-precision provider | Reconciled (and superseded in round 3) |
| 2.3 | Two of five per-provider constraints were dropped, including the free-tier/paid-tier split that affects a published quality column | All five restored; footnote added |
| 2.4 | Appendix B promised a four-field schema and delivered two; no "how invoked" field anywhere, and the framework that forced the judge change was never named | Module map added, "how invoked" column added, framework named |
| 2.5 | The narration table's footnote 4 described the time-to-first-audio protocol but was attached to real-time factor, a different measurement | Separate footnote 11 created |
| 2.6 | The completion checklist and preamble did not cover everything needing filling — config snapshot, reference verification, reduced judgment counts, budget-driven corpus reduction, drift analysis | Five checklist rows added; preamble corrected |
| 2.7 | References: a malformed model URL, a doubtful dual venue, an authorless entry, an unverified benchmark that a research question depends on, and no citation markers anywhere in the body | Corrected, flagged, and the unanchored-citations problem stated (see also 3.8, 3.10, 3.13) |
| 2.8 | Reproduction cost misstated the pilot's basis and undercounted paid accounts | Corrected |
| 2.9 | "The y-axis of both frontier charts" against four charts elsewhere | Corrected to four |
| 2.10 | Corpus described as "written for this study" and "guaranteed absent from training data" — neither accurate | Weakened to what the design supports (strengthened again in 3.36) |
| 2.11 | Six overclaims: a hypothesis asserted as a demonstration, an unqualified novelty claim, a superlative about a third-party toolkit, an undated leaderboard standing, an uncited staleness claim, and two literature characterisations with no sampling frame | All hedged or removed |
| 2.12 | A self-directed review described as "independent", and the substantive-findings grouping contradicted the spec's | Both corrected |
| 2.13 | **An inverted gate.** Real-time factor was defined as synthesis time ÷ audio duration (lower is faster) while the narration gate read "RTF > 3×" — which would have selected the *slowest* systems | Definition inverted in both documents, direction stated explicitly, checklist item added |
| 2.14 | Contribution claimed the two-judge design "repairs" a confound the appendix says it only reduces | Corrected |
| 2.15 | Table column counts drifted from headers after column removals | All tables validated |
| 2.16 | Front matter claimed all appendices populated; one is entirely placeholder | Corrected |
| 2.17 | Assorted writing defects: a dimension list of seven called eight, a first-person sentence in an impersonal document, duplicated sentences between body and appendix | Fixed |

## 3. Round 3 — full re-review, four independent passes (45)

### 3A. External facts, verified live (16)

The most consequential category: claims about third-party tools, models and benchmarks
that were confidently stated and wrong.

| # | Defect | Fix |
|---|---|---|
| 3.1 | **Judge 1 could not be loaded as specified.** The plan dropped NVIDIA NeMo on the premise that Parakeet TDT loads from HuggingFace `transformers` — but `ParakeetForTDT` exists only on `main`, and NVIDIA's own model card says it must be installed from source until it reaches a release. Depending on an unreleased revision would have undercut the claim that the lockfile pins the measuring instrument | **Judge 1 switched to Parakeet RNNT 0.6B**, which shipped in a release and pins by version. Same encoder family, same organisation, same training pipeline — the independence argument is untouched. Phase B re-checks whether TDT has landed |
| 3.2 | **The comparison board's methodology claim was false.** The spec asserted its latency figures are "spec-sheet numbers with no published measurement methodology — no region, percentile, trial count, or streaming mode". It publishes the median of 50 sequential live streaming trials, measured not vendor-supplied, with per-model date stamps. Three of the four things claimed missing are published | Positioning rewritten. Only the region is genuinely absent. **RQ3 reframed from an audit into a like-for-like replication**, which is a stronger question, with the coverage limit (at most three of six systems) stated |
| 3.3 | **The staleness exhibit was false.** The spec claimed the board still ranks a provider whose platform shut down in 2025. It does not | Withdrawn explicitly rather than deleted, and replaced with the board's own per-model `checked` dates as the evidence for staleness |
| 3.4 | Parakeet described as "topping the Open ASR leaderboard" — an undated claim about a contested and fast-moving standing | Reframed around throughput, which is what judge selection actually needs, with the accuracy claim dropped |
| 3.5 | **NISQA described as "a telephony degradation model, not a naturalness judge"** — false; the project ships a NISQA-TTS head explicitly for naturalness. A construct-validity error inside a construct-validity argument | Corrected to the accurate objection: NISQA-TTS saturates for the same reason UTMOS does, and its main model measures a different construct |
| 3.6 | Hosted inference costed at ~$0.08/generation against a verified ~$0.003 — 24× high. This had caused a real design concession: one provider's variance subset was cut in half to save money that did not need saving | Full subset restored for all six; budget corrected |
| 3.7 | The benchmark's minimum sample size was treated as an open Phase B question. It is published: 50–100 samples suffice | Question closed; 75 items per use case now has a documented justification rather than an intuition. **Consequence:** the split-half check moved off a 5-item pilot, which sits far below that floor |
| 3.8 | A dual-venue citation was flagged as impossible. It is two companion papers by the same authors at two venues | Resolved; both cited, with the institution named |
| 3.9 | The distributional metric requires a **noise** reference in addition to a speech reference, and warns that results are best when speaker identities match — a stronger constraint than the domain match the docs planned for | Both added to the pre-registered configuration requirements |
| 3.10 | The secondary quality model described as producing two axes; it produces four | Corrected, and **which axes are reported is now pre-committed** — reporting four unlabelled would invite post-hoc selection |
| 3.11 | An unsourced "everything scores 4.3–4.6" saturation figure | Removed and replaced with the benchmark's own published correlation evidence |
| 3.12 | Toolkit metric count stated as "80+"; neither published figure is 80 (65 with 729 variations in the paper, 90+ in the README) | Both cited with dates |
| 3.13 | The loudness library described as implementing "EBU R128"; it implements ITU-R BS.1770-4, which R128 is built on. Separately, −18 LUFS was phrased as though it came from the standard (R128 broadcast is −23) | Both corrected |
| 3.14 | One provider's monthly credit allowance understated by ~21% | Corrected |
| 3.15 | One provider's streaming path described as "Preview" status; it went generally available in April 2025, and its documentation shows streaming synthesis. The buffered-REST fallback — which disfigures the latency table with a non-comparability footnote — may be unnecessary | "Preview" removed; Phase C now tests streaming for fifteen minutes before committing to the fallback |
| 3.16 | The judge-independence claim was asserted rather than cited, though NVIDIA's own paper states the shared encoder and shared training set directly | Citation added, converting the project's strongest methodological assertion into a receipt |

### 3B. Statistical and methodological errors (10)

| # | Defect | Fix |
|---|---|---|
| 3.17 | **The domination rule was the wrong test on the wrong quantity.** Non-overlap of marginal 95% intervals corresponds to roughly p<0.006 — far more conservative than intended — and Bradley–Terry strengths come from one joint fit, so they are correlated and identified only up to the anchoring constraint. Marginal intervals are not the right object | **Domination now tested on the bootstrap interval of the pairwise difference**, requiring it to exclude zero |
| 3.18 | **"Indistinguishable at this n" converted absence of evidence into a positive finding**, and had a dedicated results column | Renamed **"no difference detected at this n"** throughout, with an explicit statement that failure to detect is not evidence of equality |
| 3.19 | **The noise-floor rule was incoherent by a factor of ~17.** It applied 2× a *per-generation* standard deviation to provider *aggregates over 75 items*, which would have suppressed essentially every real difference — the exact opposite of its stated purpose. The multiplier was also unjustified, the scope unbounded, and pooling assumed a homoscedasticity the data was meant to test | Restated at the level actually reported (1.96 × the standard error of the difference of aggregates), scoped explicitly to the two metrics where variance is measured, reported per provider rather than pooled, with its own uncertainty published |
| 3.20 | The bootstrap's resampling unit was never stated; resampling judgments independently ignores clustering by item and session and understates intervals. Degenerate resamples (all-win records) would break the fit silently | Clustered bootstrap specified, penalty term added, affected fraction reported |
| 3.21 | **No power analysis for the axis the entire design rests on.** The study pre-committed to an interval-based decision rule without ever estimating the interval width the judgment budget produces | Minimum detectable difference now simulated before the campaign at both 210 and 126 judgments and recorded as a pre-registered power statement |
| 3.22 | **Gates had no defined behaviour for structurally unmeasurable inputs.** Two of six systems can neither pass nor fail the conversational latency gate, leaving a third of the roster undefined for the study's primary research question | `na_policy` per gate with three explicit values; "not assessed — reason" added as a reportable status |
| 3.23 | The two-judge agreement rule — the headline methodological claim — had **no operational definition**. "Errors both judges hear" is not implementable: no intersection procedure, no handling of insertions, no band cut-points, no defined statistic, and no detectors for the four catastrophic-event types being published as counts | Full algorithm specified: per-reference-token error indicators, intersection, ±1-token window for insertions, a named lower-bound statistic, pinned normaliser, band cut-points in config, and four concrete event detectors |
| 3.24 | The per-item failure threshold was called "pre-committed" in four places with no value anywhere | Committed: agreement error rate above 5%, or any agreed error inside a numeric, currency or date span |
| 3.25 | **Re-running failed generations would bias failure incidence downward by exactly the events it counts**, with no rule separating transport failures from content failures | Pre-committed: transport failures re-run and logged, content failures counted and never replaced |
| 3.26 | Rank correlations were asked to license conclusions they cannot support — at n=4 even a perfect correlation cannot reach significance — and the unit of analysis was never fixed | Power limit stated in advance, board comparisons demoted to qualitative concordance, and the item-level comparison (n in the dozens) pre-registered as the confirmatory one |

### 3C. Executability and risk (9)

| # | Defect | Fix |
|---|---|---|
| 3.27 | **Week 1's exit criterion required phases scheduled for weeks 2 and 3.** The "$1 pilot end-to-end through to a toy frontier chart" needs the human layer for its y-axis, the cost analyzer for its x-axis, and the scoring and reporting commands to render | Split into Pilot-1 (week 1: generation, quality, hygiene — enough to test that gates discriminate) and Pilot-2 (end of week 2: the frontier) |
| 3.28 | **The free-tier data is irreversible and nothing validated it before the window closes.** Ordering a provider first is not a mitigation for irreversibility — and the project has already shipped one silent defect that corrupted every duration-dependent metric | Four mitigations: run that provider's campaign as soon as its adapter is green rather than waiting for the harness; a mandatory decode-and-validate acceptance gate before a fixed date; off-site backup; and a pre-committed fallback if the campaign has not completed in time |
| 3.29 | The hour budget is roughly 2× over, and it breaks in week 3 where the decision layer, the remaining judgments, and six pages of writing collide | Stated in the spec rather than discovered, with a **pre-committed cut list in priority order**: admin panel, hosted rating stack, robustness sweep, secondary quality model. The writing, the uncertainty machinery and the deadline are never cut |
| 3.30 | **The pre-registration receipt could not fail.** Results are gitignored, so "the tag predates all result files in git history" is vacuously true and proves nothing — the project's central credibility claim rested on an untestable check | Analysis and decision artifacts now committed; per-run manifest hashes committed; the check rewritten as a falsifiable assertion the report tool enforces |
| 3.31 | **The anchor was to be the rater's own voice**, which defeats blinding entirely for the one clip that pins the top of the scale | Third-party or public-domain anchor required; if unobtainable, the unblinding is disclosed and the anchor drops out of the scale definition |
| 3.32 | The consistency re-judge requires a week's gap the three-week schedule cannot provide for judgments made in week 3 | Re-judge set designated at the first session in week 2, re-judged on a fixed date; achieved gap reported as measured |
| 3.33 | **The rating interface would have published ~200MB of six providers' generated audio plus a human recording to an open URL** — a token in a query string is not access control — contradicting the appendix that claims private results removed the redistribution question | Rating page runs locally for v1. Removes the exposure, the hosting decision, the form backend and several hours of build at once |
| 3.34 | The developer-experience measurement could not be taken for one provider (its adapter predates the metric's definition), and the specified protocol differs from what the build actually does | Separate throwaway session per provider before its production adapter; the missing one re-run |
| 3.35 | The risk table was technically strong and operationally empty — no schedule slack, no data-loss story, no provisioning failure path, no minimum-viable outcome, no owner for applying the amendments the plan itself proposes | Seven execution risks added with concrete mitigations, including a stated minimum-viable deliverable |

### 3D. Consistency, specification and structure (10)

| # | Defect | Fix |
|---|---|---|
| 3.36 | The spec still claimed the corpus is "guaranteed absent from any provider's training data" while the report had already weakened it; and the items are partly machine-drafted, which is material to the contamination probe | Both aligned on the weaker, supportable claim, with the generation method disclosed |
| 3.37 | **The model string was never pinned per use case.** Generation was specified "at the provider's highest quality tier", which would have made the latency leaders fail the conversational gate by construction of our own protocol | Model now selected and locked per `(provider, use case)` on the same recommended-by-the-provider rule as voice |
| 3.38 | One system's quality and latency come from different model strings, so its frontier point corresponds to no deployable configuration — disclosed only in a table footnote | Annotation required **on the chart itself** |
| 3.39 | "Noise floor" named two different quantities — a statistical standard deviation and an acoustic dBFS measurement — in adjacent gate rows in the same config file | Renamed `measurement_noise_floor` and `acoustic_noise_floor_dbfs` |
| 3.40 | The conversational latency gate's rationale justified 500ms while the gate was 400ms, and the ±20% robustness sweep could never reach 500ms — so the document's flagship robustness example fell outside its own sweep | Rationale rewritten as deliberate headroom; sweep replaced with explicit `robustness_points` |
| 3.41 | Three definition-of-done lists had drifted: "both frontier charts" against four, and two enforcement clauses present in one list and missing from another | Reconciled; four charts everywhere |
| 3.42 | Analyzer module count stated as six against seven listed; box count as nine against ten | Both corrected |
| 3.43 | **The diagram showed the pre-registered gates never reaching the decision layer** — the only config edge went to the runner — and its store path could not represent use case or draw index, so campaign and variance outputs would collide | Config edges to analysis and scoring added; store path corrected; the board snapshot given a home |
| 3.44 | The narration results table used the conversational column set and could not display the evidence for its own gates; both tables were also sorted by a point estimate the design says cannot be ordered | Two distinct column sets specified; row order grouped by status with an explicit statement that it carries no quality claim |
| 3.45 | The research report had **no ethics or consent statement, no data availability statement, no funding or competing-interests declaration, no author-roles statement, and no falsification criteria** — despite recording a human voice, collecting judgments from a named person, buying subscriptions from vendors under test, and having one person occupy every role | Sections 8A and 8B added covering all five, including the concentration-of-roles limitation |

---

## 4. Pattern notes

Three patterns account for most of the volume, and each is worth carrying into the build.

**Inherited claims decay.** Nine of the sixteen factual defects in round 3 were true, or
plausibly true, when the source documents were written, and had simply not been re-checked.
Every external claim in the current set now carries a verification date, and the analysis-day
re-verification rule that already applied to pricing has been extended to capability and
benchmark claims.

**Statistical machinery added under time pressure is where the real errors live.** The
uncertainty apparatus was added in response to a review finding — and three of its four
components were wrong on first implementation: the wrong test, the wrong estimand, and a
threshold off by an order of magnitude. Adding rigour is not the same as adding correct
rigour, and the second is only established by someone checking.

**Documents drift apart at exactly the numbers that matter.** Every count that appeared in
more than one document diverged at least once. The current set has been swept for
cross-document agreement on every quantitative and protocol claim; the durable fix is that
each number should live in exactly one place — the pre-registered configuration — and be
quoted from there rather than restated.

---

## 5. Open items — not defects, decisions or verifications still outstanding

These are flagged rather than fixed, because they need either a decision or an
external check that cannot be made from the desk.

1. **Whether the comparison board's coverage supports RQ3 at all.** At most three of six
   systems carry a measured latency there. If that proves to be fewer, RQ3 should be
   dropped from the pre-registered design rather than quietly abandoned later.
2. **The open-weights model's licence is ambiguous** — its model card says Apache-2.0, the
   comparison board reports a Llama community licence. It is the one roster member where a
   restrictive term could bite. Resolve in Week 1.
3. **Whether the free and paid model strings of the value-tier provider share weights.**
   Determines whether its quality row carries a caveat in every table.
4. **Whether the hyperscaler's streaming path works**, which would remove a
   non-comparability footnote from the entire latency table.
5. **Whether Parakeet TDT has reached a `transformers` release** by Phase B; if so it
   replaces RNNT as judge 1.
6. **The reference and noise corpora for the distributional metric**, including how to
   handle its speaker-identity guidance against a design that locks a different voice per
   provider.
7. **All references remain unverified** against the published record, and no citation
   markers exist in the report body.
8. **The free-tier deadline that sets the whole schedule has already moved more than once.**
   Worth one sentence in the write-up, and worth not over-fitting the plan to a date that
   may shift again.
