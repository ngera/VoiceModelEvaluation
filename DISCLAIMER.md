# Disclaimers, scope, and reader-safety notes

This document sets the ground rules for reading anything in this
repository. Every claim in
[04_RESULTS.md](documentation/04_RESULTS.md),
[05_CASE_STUDY.md](documentation/05_CASE_STUDY.md),
[06_KEY_FINDINGS.md](documentation/06_KEY_FINDINGS.md), and the
per-test writeups under [analysis/verification/](analysis/verification/)
should be read subject to the scope below.

---

## Time-boundedness

**All findings are as of 2026-09-01.** Voice AI vendors ship model
updates on the order of weeks to months. A finding about `tts-1-hd`,
`Simba-3.2`, `sonic-2`, `eleven_flash_v2_5`, or
`lucataco/orpheus-3b-0.1-ft` at the version SHAs we tested may not
transfer to whatever the same vendor ships next quarter. Every
adapter records the exact model string it called; the campaign
`manifest.json` files record the exact date and version pins used.

Before making a vendor decision on the strength of findings here,
re-run the evaluation against the vendor's *current* model — the
whole repo is designed to make that a `veval generate` + `veval
analyze` away.

---

## No vendor affiliation

The authors of this evaluation have **no financial or contractual
relationship with any of the vendors evaluated** (ElevenLabs,
Cartesia, Fish Audio, Google Cloud, Deepgram, Canopy Orpheus / lucataco,
OpenAI, Speechify). We are not compensated by any vendor. No vendor
provided free credits, discounted access, or advance previews for
this project. No vendor reviewed the findings before publication. No
vendor's marketing or PR team has any input into the language used
here.

All API access was on **publicly-listed pricing tiers** at the time
of testing (see [configs/pricing.yaml](configs/pricing.yaml)).
**Signup credits available to any new customer** were used where
applicable (notably Deepgram's $200 signup credit for new accounts,
which fully absorbed our Deepgram spend across the campaign +
verification runs). **No vendor negotiated preferential pricing,
provided out-of-band credits, or discounted access.**

**Reproduction cost, not project accounting** — this repository
reports vendor *pricing* (D6, [04 § Cost calculus](documentation/04_RESULTS.md#cost-calculus))
because per-1K-word rates are a finding a reader acts on. It does
**not** report what running the study cost its author: that is
neither a finding nor a scope condition, and publishing it invited
the reader to weigh the work by its budget rather than its method.
What a reader does need is what re-running it would cost *them* —
reproducing the primary campaign alone lands in the **$5–15**
band, and reproducing every committed run in the **$15–30** band,
depending on account tiers, credit balances, and vendor pricing on
the day. [03 § Reproduce the published evaluation](documentation/03_RUNBOOK.md#reproduce-the-published-evaluation)
carries the per-phase breakdown.

**Artefact availability** (unchanged by the above): per-run cost
models are committed as `analysis/*/cost_model.json`, except the
doctor-probe/pilot line and the T4 / T8 / Wave-4b lines, which
live in `runs/<id>/api_log.jsonl`. That path is gitignored
(regenerable, not versioned; see [.gitignore](.gitignore)), so
re-deriving those two `cost_model.json` files needs either a fresh
`veval generate` or the original `runs/` tree on disk.

---

## Scope: specific accounts, specific voices, specific tiers

Every measurement in this repository was taken from a specific
combination of:

- **Vendor account** at a specific paid tier (e.g., Speechify Starter
  $10/mo, ElevenLabs Creator, Cartesia Pro $5/mo, Deepgram $200
  signup credit, OpenAI Tier 1, Replicate pay-per-use). Enterprise
  contracts, annual commits, and volume-negotiated tiers may produce
  materially different behavior on rate limits, latency SLAs, cost
  per unit, and model access.

- **One voice per vendor per use case** — locked in
  [configs/voices.yaml](configs/voices.yaml) before results
  existed. Two additional voice tests followed: T6 for Speechify
  (`edmund_32` vs pinned `geffen_32` on conversational,
  cross-gender; `edmund_32` vs pinned `wyatt_32` on narration,
  same-gender), and Phase 2 Follow-up 4 for OpenAI (onyx →
  nova), Fish, Deepgram (orion → luna), and Google (Charon →
  Kore) — all cross-gender against the pinned. Cartesia +
  ElevenLabs + Orpheus have no alt-voice measurement (inferred,
  not measured). See F-7 for the full paired-z + gender
  discussion.

- **One measurement environment** — residential Windows 11, home
  broadband, single geographic region. Absolute latency numbers are one point in a
  session-to-session distribution (see F-11 — a third session with
  concurrent ping baseline showed we cannot treat any single
  session as a ceiling in either direction). **Vendor rankings**
  on latency are portable across sessions; **absolute values** are
  not. See
  D-G in [06_KEY_FINDINGS.md § decisions](documentation/06_KEY_FINDINGS.md#decisions)
  for the full rationale.

**Any finding here that names a vendor is a finding about *our
specific tested configuration of that vendor*, not a universal
statement about the vendor's technology.** A different voice_id, a
different account tier, a different serving region, or a different
version of the model may produce a different result. Where a finding
is likely to generalize, we say so explicitly. Where it is likely
tied to the specific test conditions, we say that too.

---

## Not legal or contractual advice

This repository is a **scoped vendor advisory** — its structure
(Q1/Q2/Q3 decision framework, cost tie-break table, per-use-case
cheat sheet) is designed to inform a TTS vendor-selection decision
under the test conditions above. What it does **not** constitute is
**legal, contractual, financial, or fiduciary advice**. The findings
are one team's measurements of publicly-available services on
publicly-available audio content, presented as reproducible data
with source code, structured to help a reader reason about the
trade-offs — not as a substitute for a professional in any
licensed category.

A PM or engineer reading this should:

- **Verify** any finding that would drive a >$10K/year vendor
  commitment by running a pilot on your own content, your own
  account tier, and your own deployment environment
- **Cross-check** vendor pricing and terms via the vendor's own
  documentation as of your buying date (our pricing.yaml is a
  snapshot; vendors change pricing periodically)
- **Consult** legal / procurement / security counsel for any
  contract-related decisions

---

## Language and framing

We describe measurement results in engineering terms where possible
(e.g., "peak amplitude ≥ 1.0 causes downstream ASR to fail" rather
than "audio is bad"). Where subjective language is used, it is:

- Backed by a specific quantitative measurement in
  [analysis/verification/](analysis/verification/) or an
  `analysis/*.json` output
- Attributed to the specific quality-rater or measurement that
  produced it (e.g., "DNSMOS OVRL ranks Fish #8 of 8 on
  conversational" rather than "Fish sounds bad")
- Softened in the technical reports (04, 06, 02, 01, 03) where
  the underlying evidence is indirect — e.g., "elevated noise floor
  per hygiene analyzer" rather than "audible hiss," since we did
  not conduct the manual listen. **The plain-language doc (08) and
  the docs/index.html brief map the `mean_noise_floor_dbfs` reading
  onto a graded listener rubric.** The mapping (as canonicalised in
  08 § 9): ≤ −55 dBFS = "very quiet, professional"; −54 to −48 =
  "quiet, broadcast-clean"; −47 to −41 = "slight audible hiss";
  −40 to −36 = "audible on quiet phone systems"; ≥ −35 = "loudest
  background — most audible hiss". Each vendor's row is phrased in
  listener terms because the target audience is non-technical
  readers deciding on a vendor and the dBFS values aren't
  self-interpreting on their own. The technical docs stay at
  "hygiene analyzer measurement" phrasing without the listener
  claim. Both are traced to the same `hygiene.json`
  `mean_noise_floor_dbfs` field; the mapping itself is not a
  measurement, it is a plain-language interpretation authored to
  make the numbers legible.

If any specific claim reads to a vendor or a reader as unfair or
factually incorrect: please open an issue on the repository with
the specific claim and the specific correction. Corrections are
logged in [CORRECTIONS.md](CORRECTIONS.md) (retractions of
claims the data falsified) or [DEVIATIONS.md](DEVIATIONS.md)
(pre-registered amendments made before results existed) — see
CORRECTIONS.md for the distinction. Corrections are made publicly
with an audit trail, never silently.

---

## Contact for corrections

Neeraj Gera · [neeraj.gera@outlook.com](mailto:neeraj.gera@outlook.com)

Public issue tracker (preferred for factual corrections):
[github.com/ngera/VoiceModelEvaluation/issues](https://github.com/ngera/VoiceModelEvaluation/issues)
