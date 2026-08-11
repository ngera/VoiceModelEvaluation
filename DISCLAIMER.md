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

**All findings are as of 2026-08-11.** Voice AI vendors ship model
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

All API access was paid-tier via publicly-listed pricing at the time
of testing (see [configs/pricing.yaml](configs/pricing.yaml)). Total
project spend across all 8 vendor accounts was approximately $56 USD.

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
  [configs/voices.yaml](configs/voices.yaml) before results existed.
  We tested a second voice for Speechify only (T6, `edmund_32` vs
  `geffen_32`). Other vendors' alt-voice behavior is inferred, not
  measured.

- **One measurement environment** — residential Windows 11, home
  broadband, single geographic region. Absolute latency numbers are
  upper bounds; enterprise deployments in a cloud VM colocated with
  each vendor's serving region are expected to see 10-30% lower
  absolute TTFA. **Vendor rankings** on latency are portable;
  **absolute values** are explicit ceilings. See
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

## Not advice

Nothing in this repository constitutes **legal, business,
investment, or purchasing advice**. The findings are one team's
measurement of publicly-available services on publicly-available
audio content, presented as reproducible data with source code.

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
- Softened where the underlying evidence is indirect (e.g., "elevated
  noise floor per hygiene analyzer" not "audible hiss," since we
  did not conduct the manual listen)

If any specific claim reads to a vendor or a reader as unfair or
factually incorrect: please open an issue on the repository with
the specific claim and the specific correction. Corrections will be
made publicly with an audit trail in
[DEVIATIONS.md](DEVIATIONS.md), never silently.

---

## Contact for corrections

Neeraj Gera · [neeraj.gera@outlook.com](mailto:neeraj.gera@outlook.com)

Public issue tracker (preferred for factual corrections):
[github.com/ngera/VoiceModelEvaluation/issues](https://github.com/ngera/VoiceModelEvaluation/issues)
