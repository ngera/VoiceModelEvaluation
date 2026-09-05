"""Slug + relative-link check across the doc set.

Reads every markdown + html file under the repo's live-doc roster
(README, DISCLAIMER, documentation/*, docs/index.html, CORRECTIONS,
analysis/round*-vs-round*-comparison.md), collects every
inbound Markdown link that points at a fragment (e.g.
`04_RESULTS.md#rankings-summary`) or a local anchor (e.g. `#f-8`),
and verifies the fragment exists as either a `## Heading` slug
(GitHub Markdown auto-slug) or an explicit
`<a name="..."></a>` anchor.

Prints one line per broken link with source file + line + target,
and exits nonzero if any broken link is found.

The user's R26 T3 note pointed out three of the last four rounds
introduced a broken internal link in text added that round. This
check is meant to be a pre-commit gate against that pattern.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path("c:/cursorProjects/voiceAgentEvals")

# Files that count as "live docs" — links from these get checked,
# and headings inside them are what those links can resolve to.
LIVE_DOCS = [
    ROOT / "README.md",
    ROOT / "DISCLAIMER.md",
    ROOT / "CORRECTIONS.md",
    ROOT / "DEVIATIONS.md",
    *sorted((ROOT / "documentation").glob("0[1-8]*.md")),
    *sorted((ROOT / "documentation").glob("EXPERIMENTS_*.md")),
    ROOT / "docs" / "index.html",
    *sorted((ROOT / "analysis").glob("round*-vs-round*-comparison.md")),
]

# GitHub Markdown slug: lowercase, strip punctuation, spaces -> hyphens
_SLUG_STRIP = re.compile(r"[^\w\s-]")


def github_slug(heading: str) -> str:
    """Approximation of GitHub's auto-slug for a Markdown heading.

    GitHub preserves consecutive spaces as consecutive hyphens
    (e.g. `F-6 · Monotonic…` becomes `f-6--monotonic…`, double
    hyphen where the `·` was stripped between two spaces). So we
    strip punctuation without introducing collapsed whitespace,
    then map each space to exactly one hyphen — NOT collapsing
    runs of whitespace first.
    """
    s = heading.strip().lower()
    s = _SLUG_STRIP.sub("", s)
    s = s.replace(" ", "-")
    return s


def collect_targets(path: Path) -> set[str]:
    """Return the set of anchor slugs that resolve inside `path`.

    Covers (a) `## Heading` auto-slugs, (b) explicit `<a name="x">`
    HTML anchors, (c) explicit `id="x"` HTML attributes in html files.
    """
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    out: set[str] = set()

    # Markdown headings — # through ######
    for m in re.finditer(r"^(#{1,6})\s+(.+)$", text, flags=re.MULTILINE):
        out.add(github_slug(m.group(2)))

    # <a name="..."> explicit anchors
    for m in re.finditer(r'<a\s+name="([^"]+)"', text):
        out.add(m.group(1).lower())

    # id="..." in html files (or Markdown blocks with raw html)
    for m in re.finditer(r'\bid="([^"]+)"', text):
        out.add(m.group(1).lower())

    return out


# link_re: markdown [text](target) — target may be relative path + optional #frag
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# code-span/code-block regions to strip before link matching. A `[text](x)`
# that appears inside `single-backticks` or a ``` fenced block ``` is prose,
# not a live link — including it produces false positives on docs that
# describe the link syntax (this file's own commentary is one such source).
_CODE_STRIP = re.compile(
    r"```.*?```|`[^`\n]+`",
    re.DOTALL,
)


def check_links() -> int:
    # Pre-cache every live doc's set of anchors
    anchors_by_path = {p: collect_targets(p) for p in LIVE_DOCS}

    broken = 0
    for src in LIVE_DOCS:
        if not src.exists():
            continue
        raw_text = src.read_text(encoding="utf-8")
        # Blank out code spans / fenced blocks so their prose can't
        # false-positive as live links. Preserve char positions with
        # spaces (line-count math elsewhere depends on this).
        text = _CODE_STRIP.sub(lambda m: " " * (m.end() - m.start()), raw_text)
        lines = raw_text.splitlines()
        for m in LINK_RE.finditer(text):
            target = m.group(1)
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            # split off fragment
            if "#" not in target:
                # no fragment — check file existence only
                path_part = target
                frag = None
            else:
                path_part, frag = target.split("#", 1)

            # resolve relative to src's directory
            if path_part:
                resolved = (src.parent / path_part).resolve()
            else:
                # bare "#anchor" — self-link
                resolved = src.resolve()

            if not resolved.exists():
                line_no = text[:m.start()].count("\n") + 1
                print(f"BROKEN FILE {src.relative_to(ROOT)}:{line_no}  target={target}  resolved={resolved}")
                broken += 1
                continue

            if frag is None:
                continue

            # only anchor-check files in the live-doc set
            if resolved not in {p.resolve() for p in LIVE_DOCS}:
                continue

            anchors = collect_targets(resolved)
            if frag.lower() not in anchors:
                line_no = text[:m.start()].count("\n") + 1
                # show a bit of context
                ctx = lines[line_no - 1].strip()[:100]
                print(f"BROKEN ANCHOR {src.relative_to(ROOT)}:{line_no}  target=#{frag}  in={resolved.name}")
                print(f"  ctx: {ctx}")
                broken += 1

    if broken == 0:
        print("all internal links OK")
    else:
        print(f"\n{broken} broken links total")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(check_links())
