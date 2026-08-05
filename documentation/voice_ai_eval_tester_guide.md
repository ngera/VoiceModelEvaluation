---
title: Tester Welcome Pack — Communications & Step-by-Step Guides
project: Voice AI Provider Evaluation
audience: External participants (non-technical wording throughout)
usage: Each section below is self-contained — copy the relevant section into an email or message when inviting someone. Replace [PLACEHOLDERS] before sending.
---

# Tester Welcome Pack

## About this project (shared intro — include in every invite)

Hi — thanks for helping out!

I'm running an independent, open evaluation of AI voice generators (the technology that turns text into spoken audio — the voices you hear in customer-service calls, audiobooks, and navigation apps). Companies that make these voices publish their own impressive numbers; my project measures them independently and publishes everything: the results, the methods, and the raw data, so anyone can check the work.

There are three ways to help, and they need very different amounts of time and skill:

| Role | What you do | Time | Skills needed |
|---|---|---|---|
| **Rater** | Listen to pairs of voices, pick the more natural one | ~20 min | None — just ears and headphones |
| **Reproducer** | Run the test kit on your computer to confirm it works | ~30–45 min | Comfortable following copy-paste computer instructions |
| **Contributor** | Add test sentences, spot errors, or extend the toolkit | Ongoing, your pace | Varies — from writing sentences to writing code |

Everything below explains each role step by step. Questions at any point: [YOUR EMAIL].

---

## Communication plan — which channel for what

The rule of thumb: **invites go where the person already is; support goes where the problem is visible; announcements go where they can be linked forever.** Don't create a community space (Discord/Slack) at this scale — it's a maintenance burden that goes quiet and looks dead; a group of under ~30 active people runs fine on direct messages + GitHub.

### Channels by audience

| Audience | Invite | Doing the task | Support / questions | Updates & results |
|---|---|---|---|---|
| **Raters** (friends/colleagues) | Personal channel they already share with you — WhatsApp/text/DM for friends, email for colleagues. Never a group blast; individual messages get 3–5× the response rate | The tokened web link — works on phone, no account, no install | Reply in the same thread they were invited in (lowest friction for non-technical people) | One thank-you message with the results link when published; nothing else |
| **Raters** (strangers, post-launch) | Public call in the launch post + results site; interested people request a link via a short form | Same tokened web link | Email only ([YOUR EMAIL]) | Opt-in checkbox on the form for "email me each monthly cycle" |
| **Reproducers** (alpha, 3–5 people) | Personal email with the packet below — this is a real favor; make the ask personal | The repo README | **Email with screenshots**, plus a 15-min call standing offer if truly stuck — do NOT force non-GitHub people into GitHub issues | Personal thank-you + credit confirmation by email |
| **Contributors** (public) | Passive: CONTRIBUTING.md, launch post, a "contributions welcome" note on the results site | GitHub (PRs, issue forms); the no-code lanes get web forms so a GitHub account is only needed where unavoidable | GitHub issues (public, searchable — support answers become documentation) | Watch/star the repo; monthly changelog is the newsletter |
| **Providers** (right-of-reply) | **Formal email to their official/support/press contact**, one week pre-publication — professional tone, dated data attached, correction window stated | — | Dedicated email thread per provider; corrections tracked as public GitHub issues once resolved | Same email thread: link when results go live |

### Cadence (per campaign cycle)

| When | Message | Channel |
|---|---|---|
| T−2 weeks | Alpha reproducer invites (individually) | Personal email |
| T−1 week | Rater invites (individually) · provider right-of-reply notices | DM/text/email · formal email |
| T−3 days | One gentle rater reminder to non-starters — **one only**, then let it go | Same thread as invite |
| T = publish | Launch post · thank-you notes with results link to every participant | LinkedIn/X + Show HN · personal channels |
| T+monthly | Drift changelog entry; new rating links to opted-in raters | Site/repo · email |

**Two etiquette rules that protect response rates:** every ask names its time cost up front ("20 minutes", "30–45 minutes") — people say yes to bounded asks; and every participant hears back exactly twice — a thank-you when they finish, and the link when results publish. Silence after someone does you a favor is how you lose them for cycle two.

---

# Packet 1 — For Raters ("lend us your ears")

### The invitation (email/message text)

> **Subject: 20 minutes + headphones = help me benchmark AI voices**
>
> Hi [NAME] — I'm independently testing which AI voice generators actually sound most human, and the most valuable thing anyone can give this project is honest ears. No technical skill needed: you'll hear two short audio clips at a time and click which one sounds more natural. It takes about 20 minutes, on your phone or computer.
>
> Your personal link: [TOKEN LINK]
> (It's unique to you — please don't forward it.)
>
> Your name won't be published — results appear only as anonymous, combined scores. Full details on the page itself. Thank you!

### Steps to follow

1. **Find a quiet spot and put on headphones.** Phone speakers in a noisy room genuinely change the results — headphones matter more than anything else on this list.
2. **Open your personal link.** You'll see a short consent note first: your clicks are combined with everyone else's and published as anonymous totals; your name and email are never published. Tap "I agree" to continue.
3. **Listen to both clips in each pair — fully, at least once each.** They say the same sentence, spoken by two different AI voices (occasionally, secretly, a real human — that's part of the design, don't worry about spotting them).
4. **Pick the one that sounds more natural and human.** Not "prettier" or "louder" — the one you'd more readily believe was a real person. If it's genuinely a coin flip, pick anyway; forced choices are part of the method.
5. **Keep going until the page says you're done** (about 20 minutes). There's a progress bar. You can close the page and reopen your link later to resume.
6. **Optional: leave a comment** at the end if any clip struck you as weird, robotic, or impressively human — free-text impressions often explain the numbers.

### Ground rules (please!)

- **Don't ask anyone else to vote on your link** — one set of ears per link, or the statistics break.
- **Don't try to identify the companies** — the test only works blind. (You won't be able to anyway; clips are anonymized.)
- **Do it in one or two sittings**, not ten — fresh ears judge differently than tired ones, and we account for session breaks.

### What you get

- A thank-you credit on the published results page (pseudonym by default; your real name only if you ask for it).
- A link to the final results before they're public.

---

# Packet 2 — For Reproducers ("check my work")

### The invitation (email/message text)

> **Subject: Can you spare 30 minutes to try breaking my test kit?**
>
> Hi [NAME] — before I publish my AI-voice evaluation, I need proof that the whole thing runs on a computer that isn't mine. You don't need to understand voice AI: you'll follow copy-paste instructions, and either it works (great, tell me how long it took) or it fails somewhere (even better — tell me exactly where). The failure reports are honestly the more valuable outcome.
>
> It costs nothing (the demo uses free trial accounts), takes 30–45 minutes, and you'll end up with a small chart your own computer produced.
>
> Instructions: [REPO LINK]/README — start at "Quickstart."

### Steps to follow

1. **Check what you need before starting:**
   - A computer (Windows, Mac, or Linux) where you're allowed to install software
   - [Docker Desktop]([LINK]) installed — this is a free tool that packages everything the kit needs, so you don't have to install anything else by hand. The README links to its official download page and the install is click-through.
   - About 2 GB of free disk space and a normal internet connection
2. **Create free accounts at the 2–3 voice providers the demo uses** (the README lists them with direct links — currently the ones with free trial credit, so this costs $0). Each signup takes ~3 minutes and gives you an "API key" — think of it as a password that lets the kit talk to that provider. **Treat keys like passwords: don't share or post them.**
3. **Copy each key into the settings file** exactly as the README shows (`there's a template file — you fill in the blanks`).
4. **Run the three commands in the Quickstart**, one at a time, copy-paste. In plain terms they do: *(a)* check everything is connected, *(b)* generate a handful of test audio clips from each provider, *(c)* analyze them and draw a small comparison chart.
5. **Time yourself** from opening the README to seeing the chart. That number — and every point where you got stuck, confused, or had to guess — is the actual product of this exercise.
6. **Send back the friction report** (template in the README, takes 5 minutes):
   - Total time, and your operating system
   - Every point you got stuck or had to re-read something
   - The chart file, if you got one
   - Where it failed and the exact error message, if you didn't — **a failure report is a success for me**, so please don't quietly give up or feel bad about it
7. **Afterwards:** you can delete the accounts and the software, or keep the kit and play with it — it's yours to keep either way.

### If you get stuck

Stop, screenshot the screen, email me. Please **don't** spend an hour heroically debugging — "I got stuck here and it wasn't obvious why" is precisely the data I need.

### What you get

- Named credit (or pseudonym, your call) in the project's acknowledgments as an alpha tester.
- Bragging rights: your machine independently verified a published benchmark.

---

# Packet 3 — For Contributors ("make it better")

### The invitation (email/message text)

> **Subject: My AI-voice benchmark is open — want to extend it?**
>
> Hi [NAME] — my independent voice-AI evaluation is now public, and it's built to be extended. There are contribution paths that need zero code (writing test sentences, fact-checking provider claims) and ones that need some (adding new providers). Everything is reviewed publicly, every contribution is credited, and the guide below sorts you into the right lane in about two minutes.
>
> Start here: [REPO LINK]/CONTRIBUTING.md

### Choose your lane

**Lane A — Test sentences (no code, ~15 min per batch).**
The evaluation is only as good as the sentences fed to the voices. We always need fresh ones — they must be *original* (written by you, not copied from anywhere — this keeps the test fair, since providers may have trained on existing text).

1. Read the one-page corpus checklist ([LINK]): sentence types we need (numbers, dates, names, tricky words), and the rules (invented names only, no real people's personal details, nothing copyrighted).
2. Write 5–10 sentences following it.
3. Submit via the form ([LINK]) or, if you're comfortable with GitHub, as a pull request.
4. Accepted sentences enter the next monthly test cycle, credited to you.

**Lane B — Fact-checking & corrections (no code, as-and-when).**
The results table contains hundreds of dated facts — prices, feature claims, latency figures. They go stale, and providers sometimes dispute them.

1. Spot something wrong or outdated? Open a correction ([ISSUE LINK] — there's a form; no GitHub knowledge needed beyond creating a free account).
2. Include a link to the source that shows the current truth.
3. Corrections are resolved publicly and logged in the changelog — including the ones where we were wrong. That's the point.

**Lane C — Rating at scale (no code).**
Same as the Rater packet above, but ongoing: each monthly re-run needs fresh ears. Say the word and you'll get a new link each cycle.

**Lane D — Add a voice provider (code — Python).**
For the technically inclined: each provider is one self-contained file with a template to copy.

1. Read `CONTRIBUTING.md` → "Adding a provider."
2. Copy the adapter template, implement the one required function, run the conformance check (`one command — it tells you exactly what's missing`).
3. Submit a pull request including the provider's capability facts (with source links and dates — the guide has the table to fill in).
4. Your adapter ships in the next cycle, credited.

### House rules (all lanes)

- **Be factual, not adversarial.** Providers are evaluated, not attacked. Every claim needs a dated source or a measurement.
- **No secrets.** Never paste API keys, and don't submit anything confidential or copyrighted.
- **Public by default.** Contributions, reviews, and corrections all happen in the open — that's what makes the project trustworthy.
- **Credit is automatic.** Every merged contribution appears in the acknowledgments and changelog.

---

## One-page FAQ (append to any packet)

**Who's behind this?** [YOUR NAME] — it's an independent solo project; no voice-AI company funds or reviews it before publication. *(Providers get a courtesy heads-up a week before results go live so they can flag factual errors — they don't get edit rights.)*

**Is my data safe?** Raters: judgments are stored against an anonymous ID; names/emails are never published. Reproducers: your API keys never leave your computer — the kit talks directly to providers; nothing routes through me.

**Does this cost me anything?** Raters and contributors: nothing. Reproducers: nothing if you use the free-trial providers listed in the demo (that's the default path).

**Can I share the results?** Yes, once public — everything is published under an open license with a citation format on the site.

**What if I start and can't finish?** Totally fine. Partial rating sessions still count; a half-finished reproduction with a friction report is still valuable. Just let me know.

**Contact:** [YOUR EMAIL] · Issues/corrections: [REPO LINK]
