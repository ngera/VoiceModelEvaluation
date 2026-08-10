# Reproducibility plan

> _DRAFT — plan, not implementation. Approve or edit; nothing here is
> built yet. When approved, individual sections become tracked work
> items._

## Purpose

Make this repo useful to three distinct readers WITHOUT them needing
to email me for context:

1. **Another PM running a similar eval** — wants to fork, swap
   providers/corpus/gates, ship a comparable case study
2. **Another PM reviewing my results** — wants to trust or dismantle
   the methodology in 30 min without cloning
3. **Me, in 4 weeks, running a drift comparison** — wants a scripted
   path that survives a fresh laptop

Ambition ceiling: **full path — cheap docs → Docker → demo cache →
hosted deploy**. Sequenced by ROI (biggest impact first, weekend-scale
tasks before week-scale tasks).

---

## Current reproducibility state (2026-08-10)

**What works cleanly today for a fresh clone:**

| Thing | Status | Why |
|---|---|---|
| Inspect code + configs | ✅ | `git clone` gets you everything |
| Read all methodology | ✅ | Spec + plan + DEVIATIONS + friction log all committed |
| See per-analyzer outputs | ✅ | `analysis/*.json` committed |
| See prereg receipts | ✅ | `git log --tags` shows v1 → v1.9 with dated commit sha |
| Regenerate score.json / site/ from analysis | ✅ | `veval score` + `veval report` need zero API keys |
| Regenerate `analysis/*.json` from `runs/*` | ⚠️ | `runs/*/audio/` is gitignored (~5 GB); requires either fresh campaign OR shared audio archive |
| Run the WAV acceptance gate | ✅ | Pure Python, no models needed |
| Run WER analyzer | ⚠️ | Requires ~5 GB model download (wav2vec2 + faster-whisper); code works |
| Run quality analyzer | ⚠️ | Audiobox works out of the box; TTSDS2 needs external reference (DAPS ~30 GB) — currently skipped per plan v2 line 267 |
| Bradley-Terry fit | ✅ | `choix` in deps; needs a rater CSV |
| Fresh generation campaign | ❌ | Needs API keys at 8 providers (~$30 up front); no demo mode |
| Rating page | ✅ | Static HTML, opens local; needs anchor recordings for full 8-vs-1-anchor coverage |

**What blocks a fresh reproducer today:**

1. **No README** — cloner has to guess what this project is and where
   to start
2. **8 API accounts + $30 up-front** — even a smoke test requires real
   provider credentials
3. **Anchor recording is personal** — can't share my voice; a
   reproducer has to record their own before the rating loop runs
4. **~10 GB of model weights** — WER + quality first-run downloads;
   nowhere warned about this
5. **Corpus text is committed but the audio isn't** — reproducer sees
   the recipe but has to bake the cake
6. **Windows-specific gotchas silently in the friction log** —
   symlink permissions, ffmpeg-missing, thread-safety fixes we made
   are portfolio-worthy findings but a Mac/Linux reproducer won't
   know they matter to them
7. **No demo path** — someone who just wants to "see it work" has to
   provision the whole stack

---

## Tiered plan

Each level is independently valuable. Ship them in order; each
lifts the visible-craft bar without depending on the next.

### Level 1 — Docs polish (recommended first ship, ~4 hours)

**Goal**: any stranger arriving at the GitHub URL knows what this
project is, what it produces, and can inspect all findings without
cloning.

Concrete tasks:

- [ ] Rename `documentation/README_DRAFT.md` → `/README.md` after final review
- [ ] Write `/ONBOARDING.md` — "3 commands to see cached demo output;
      3 more to reproduce your own analysis"
- [ ] Expand `.env.example` with per-provider signup URLs, credit
      requirements, and "which providers can be skipped for a
      subset run"
- [ ] Add a `/QUICKSTART.md` snippet targeting each of the three
      personas explicitly ("if you're here to X, do Y")
- [ ] Add a `CONTRIBUTING.md` describing the pre-registration + DEVIATIONS
      discipline that any PR needs to respect
- [ ] Add rendered screenshots of the 5 admin pages to
      `documentation/screenshots/` and reference in README
- [ ] Populate the "Author" + LinkedIn sections in README
- [ ] Commit a **snapshot copy of `site/`** (the rendered case study +
      memos + PNGs) under a versioned subdirectory (`site_2026_08.tar.gz`
      or `docs/results-2026-08/`) so a reader without the analyzer
      stack can still SEE the outputs
- [ ] Cross-link `dx/friction_log.md` → per-provider integration
      lessons from the README

**Time**: 4 hours end-to-end (mostly writing + one screenshot pass)

**ROI**: highest per hour. This is the difference between "curious
recruiter closes the tab" and "curious recruiter shares the link."

---

### Level 2 — `veval demo` command (~1 day)

**Goal**: a reproducer can run **one command with zero API keys and
zero credit** and get a working end-to-end pipeline against a small
sample.

Concrete tasks:

- [ ] Add `demo/audio/` with ~10-20 pre-generated WAVs across 3-4
      providers (small enough to commit — MP3-compressed if space is
      tight). Legal check: some providers' TOS restricts audio
      redistribution; use fair-use short clips + attribution.
- [ ] Add `demo/manifest.json` + `demo/api_log.jsonl` mirroring the
      run store shape
- [ ] Add `demo/pricing.yaml` and `demo/analyzers.yaml` (both
      Audiobox-only, no TTSDS2 refs required) — smaller variants of
      the real configs
- [ ] Add `veval demo` CLI subcommand that:
      1. Verifies the demo cache exists
      2. Runs `analyze --stages acceptance,hygiene,latency,cost` against
         demo/
      3. Prints the mini frontier table
      4. Suggests next commands ("to run WER, download ~5 GB of models
         with `uv sync --extra analyze`; to run your own, see
         `documentation/voice_ai_eval_execution_runbook.md`")
- [ ] Documentation: "The demo takes 30 seconds and shows the pipeline
      producing real numbers on real audio. It is NOT a benchmark —
      the sample is too small — but it proves the code works before
      you commit to the model downloads or API accounts."

**Time**: ~1 day. Legal review of the redistributed audio adds
uncertainty — could be 2-3 days if we need explicit provider
permission or need to synth against a provider whose TOS is
permissive.

**ROI**: converts "curious tire-kicker" into "trusts this actually
runs." Also unblocks CI: a fully-cache-served `veval demo` can run in
GitHub Actions in <60s as a smoke test.

---

### Level 3 — Docker (~1-2 days)

**Goal**: analyzer stack reproducibility survives Python-version /
OS / library-cliff drift. Anyone running Docker can execute the full
analyzer pipeline against the demo cache OR their own campaign
without re-solving the ttsds transitive-dep cliff we already hit.

Concrete tasks:

- [ ] Write `Dockerfile.analyze` pinning Python 3.11 + torch 2.4.1 +
      transformers 4.57.6 + ttsds 2.1.3 + all the constraints from
      `pyproject.toml` `analyze` extra
- [ ] Include a `Dockerfile.demo` that pre-downloads wav2vec2 + Whisper
      + Audiobox weights into the image (larger image, faster first
      run for demo users)
- [ ] Write `docker-compose.yml` for one-command bring-up:
      `docker compose up demo` runs the demo pipeline; `docker compose
      up admin` starts Streamlit on port 8501
- [ ] Add smoke-test invocation to CI (see Level 4)
- [ ] Document platform assumptions: CPU works for demo, GPU strongly
      recommended for full-scale WER + quality on 1,200 files

**Time**: 1-2 days including CI wiring. The devcontainer we deleted
in Phase B is a decent starting point for the analyze image.

**ROI**: eliminates the "torch/torchaudio/transformers version cliff"
class of reproducer complaint. Also opens door for hosted demo
(Level 4).

---

### Level 4 — Hosted results page + auto-deploy (~2-3 days)

**Goal**: a URL a recruiter can click. Nothing to install, nothing to
run; the case study, memos, and interactive Plotly frontier render
in the browser.

Concrete tasks:

- [ ] `.github/workflows/publish-site.yml`:
      - Trigger: push to `main` matching `prereg-v*` tags
      - Steps: `uv sync --extra admin` → `veval report analysis/score.json
        --out site/` → deploy `site/` to GitHub Pages
      - Snapshot old versions per tag (so `veval.ngera.io/v1.9/` and
        `veval.ngera.io/v2.0/` both exist)
- [ ] Custom domain (optional, ~$12/yr): `veval.ngera.io` or similar
- [ ] Add a `banner.svg` + a proper index page (currently
      `case_study.md` opens on GitHub-Pages default routing)
- [ ] Optional: **read-only Streamlit demo** on Streamlit Community
      Cloud (free tier) that serves the admin panel against the
      committed `analysis/` and `demo/` data. Read-only means the
      "Run" and "Rate" pages disable their action buttons. Recruiters
      can browse the Frontier + Results interactively.
- [ ] README hero image: embed a linked PNG of the conversational-cost
      frontier so LinkedIn preview shows the chart, not just a code
      icon

**Time**: 2-3 days. Streamlit Community Cloud has usage limits + a
sleep-after-inactivity model — either accept the cold-start or run
Vercel/Fly.io on the free tier ($0-5/mo). Custom domain has an
ongoing $12/yr fee.

**ROI**: this is where the project transitions from "GitHub repo" to
"portfolio piece." A LinkedIn post that links to a URL with charts
gets ~10× the engagement of one that links to a `README.md`.

**Stop-condition alignment**: if we ship Level 4, we need to plan
the retirement clearly. Set a calendar reminder 4 months out to
either archive the site (banner + read-only) or explicitly commit to
another cycle. Otherwise it becomes the stale leaderboard we
critique.

---

## Recommended MVP: Levels 1 + 2 only (~1.5 days)

If you want to ship SOMETHING soon rather than everything:

1. Level 1 docs polish (4 hours) — 80% of the perceived-legibility win
2. Level 2 `veval demo` (~1 day) — 80% of the "does this actually run"
   win

That's a fresh clone → **useful in 30 seconds** without an account.
Levels 3 + 4 are cost-multipliers on that foundation but the diminishing
returns kick in.

Levels 3 + 4 land later if the LinkedIn post gets traction and it's
worth the maintenance commitment.

---

## Non-plan: things I explicitly do NOT recommend building

- **A pip-installable `pip install veval` package** — this project is
  a case study, not a library. Someone forking should read the
  spec + friction log first, not `import` and call. Publishing to
  PyPI would over-signal "reuse me" when the correct signal is
  "learn from me + adapt."
- **A public leaderboard site** — the spec's Appendix E is explicit
  about why: it would put me in the same business as the ones I'm
  critiquing, with the same failure mode (staleness). Retire cleanly.
- **A "provider #9 wizard"** — templating the adapter surface would
  imply I'll accept PRs to add providers. This is a portfolio
  project; the roster is frozen at 8.
- **Automated model updates** — every provider's model changes
  underneath us. The drift re-run is the answer, not an auto-refresh.

---

## Time-sequenced task list (if Level 1 + 2 + 3 + 4 all ship)

| When | Task | Effort |
|---|---|---|
| Day 1 morning | Level 1: README polish + ONBOARDING + `.env.example` expansion | 3-4h |
| Day 1 afternoon | Level 1: commit `docs/results-2026-08/` snapshot + screenshots | 1-2h |
| Day 2 | Level 2: build `demo/` audio corpus + `veval demo` command | 1 day |
| Day 3 | Level 3: `Dockerfile.analyze` + `Dockerfile.demo` + docker-compose | 1 day |
| Day 4 morning | Level 3: CI smoke test on Docker | 2-3h |
| Day 4 afternoon | Level 4: GitHub Actions publish-site workflow | 3-4h |
| Day 5 | Level 4: Streamlit Community Cloud read-only admin + custom domain | 1 day |
| Day 5 evening | LinkedIn post with the URL | 30 min |

**Total: ~5 focused days.** Realistic in ~2 weeks part-time.

---

## Open questions before executing

1. **Legal check on redistributed demo audio**: worth 15 min of
   reading TOS for the 3-4 providers we'd include in `demo/audio/`?
   Or use openly-licensed reference speech (e.g., LibriSpeech) as
   "demo synthesized" placeholders and label them clearly?
2. **Custom domain**: worth the $12/yr, or GitHub Pages default URL
   suffices?
3. **Streamlit vs static-only**: is the interactive Plotly HTML in
   `site/interactive/*.html` sufficient? A hosted Streamlit adds
   filtering + tab navigation but is another moving part to maintain.
4. **Snapshot strategy for `site/`**: commit as tarballs, commit
   plain, or use `git subtree` to a separate `gh-pages` branch?
