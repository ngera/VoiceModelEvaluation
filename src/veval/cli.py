"""veval CLI entry point.

Subcommands (implemented incrementally per Phase in CLAUDE.md):
- doctor    (Phase A) — smoke-test all/one adapter end-to-end
- generate  (Phase D) — run the corpus × providers campaign
- analyze   (Phase E) — VERSA-backed WER/quality/hygiene/latency
- score     (Phase G) — apply gates, build Pareto frontiers
- report    (Phase G) — render tables, charts, memos
"""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from veval import __version__
from veval.adapters import ADAPTERS
from veval.doctor import DoctorReport, run_doctor
from veval.runner import RunMode, Runner, RunSummary, SpendTracker, SynthesisCache
from veval.config import load_pricing

app = typer.Typer(
    name="veval",
    help="Voice AI provider evaluation harness.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _load_env() -> None:
    load_dotenv()  # reads .env from CWD if present


@app.callback(invoke_without_command=True)
def _root(
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    if version:
        console.print(f"veval {__version__}")
        raise typer.Exit()
    _load_env()


@app.command()
def doctor(
    provider: str | None = typer.Option(
        None, "--provider", "-p",
        help="Check only this provider (default: all in providers.yaml)",
    ),
    providers_file: Path = typer.Option(
        Path("configs/providers.yaml"),
        "--providers-file",
        help="Path to providers.yaml",
    ),
    voices_file: Path = typer.Option(
        Path("configs/voices.yaml"),
        "--voices-file",
        help="Path to voices.yaml (source of truth for (voice_id, model) per use case)",
    ),
    use_case: str = typer.Option(
        "conversational", "--use-case", "-u",
        help="Which use case's locked voice+model to probe (conversational|narration)",
    ),
    text: str = typer.Option(
        "The quick brown fox jumps over the lazy dog.",
        "--text",
        help="Probe text for the smoke test",
    ),
) -> None:
    """Health-check the pipeline end-to-end BEFORE spending money on a campaign.

    Verifies configs load, API keys are present, adapters can synthesize,
    and the run store writes correctly. Same spirit as `brew doctor` or
    `flutter doctor`.

    Voice + model are looked up from voices.yaml per (provider, use_case).
    For split-model providers (Fish free vs paid), the probe uses the
    free-tier `quality_model` to avoid burning paid credits on smoke tests.
    """
    if use_case not in ("conversational", "narration"):
        console.print(f"[red]--use-case must be conversational or narration, got: {use_case}[/red]")
        raise typer.Exit(code=2)

    results = run_doctor(
        providers_file=providers_file,
        voices_file=voices_file,
        only_provider=provider,
        use_case=use_case,  # type: ignore[arg-type]
        probe_text=text,
    )
    _print_doctor_report(results)

    # Non-zero exit if any adapter failed — useful for CI
    if any(not r.ok for r in results.adapter_results):
        raise typer.Exit(code=1)


def _print_doctor_report(results: DoctorReport) -> None:
    console.print()
    console.rule("[bold]veval doctor[/bold]")

    # Environment checks
    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_row("configs", results.configs_status())
    env_table.add_row("env keys", results.env_status())
    env_table.add_row("adapters registered", str(len(ADAPTERS)))
    console.print(env_table)
    console.print()

    # Per-adapter results
    adapter_table = Table(title="Adapters", show_lines=False)
    adapter_table.add_column("Provider", style="bold")
    adapter_table.add_column("Status")
    adapter_table.add_column("TTFA (ms)", justify="right")
    adapter_table.add_column("Total (ms)", justify="right")
    adapter_table.add_column("Audio bytes", justify="right")
    adapter_table.add_column("Notes", overflow="fold")

    for r in results.adapter_results:
        status = "[green]✓[/green]" if r.ok else "[red]✗[/red]"
        ttfa = f"{r.result.ttfa_ms:.0f}" if (r.ok and r.result and r.result.ttfa_ms) else "—"
        total = f"{r.result.total_ms:.0f}" if (r.ok and r.result) else "—"
        size = f"{len(r.result.audio_bytes)}" if (r.ok and r.result) else "—"
        adapter_table.add_row(r.provider, status, ttfa, total, size, r.notes)
    console.print(adapter_table)
    console.print()

    # Summary
    ok_count = sum(1 for r in results.adapter_results if r.ok)
    total_count = len(results.adapter_results)
    if ok_count == total_count and total_count > 0:
        console.print(f"[bold green]All {total_count} adapters passed.[/bold green]")
    else:
        failed = total_count - ok_count
        console.print(f"[bold red]{failed} failure(s) out of {total_count}.[/bold red] "
                      f"Fix before Phase 1 campaign.")
    if results.run_dir:
        console.print(f"[dim]Run written to: {results.run_dir}[/dim]")


@app.command()
def generate(
    mode: str = typer.Option(
        "campaign", "--mode", "-m",
        help="campaign | variance | latency (D.3/D.4 land later)",
    ),
    provider: list[str] | None = typer.Option(
        None, "--provider", "-p",
        help="Restrict to one or more provider names (default: all in providers.yaml)",
    ),
    use_case: list[str] | None = typer.Option(
        None, "--use-case", "-u",
        help="Restrict to conversational|narration (default: both)",
    ),
    items: list[str] | None = typer.Option(
        None, "--items", "-i",
        help="Restrict to specific item IDs (e.g. --items S01 --items M03). Used for the $1 pilot",
    ),
    providers_file: Path = typer.Option(
        Path("configs/providers.yaml"), "--providers-file",
    ),
    voices_file: Path = typer.Option(
        Path("configs/voices.yaml"), "--voices-file",
    ),
    corpus_dir: Path = typer.Option(
        Path("corpus"), "--corpus-dir",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache",
        help="Bypass the content-hash cache (default: cache enabled for campaign mode)",
    ),
    cache_dir: Path = typer.Option(
        Path(".cache/synthesis"), "--cache-dir",
    ),
    variance_subset_file: Path = typer.Option(
        Path("corpus/variance_subset.yaml"), "--variance-subset-file",
        help="Item IDs for --mode variance (default: prereg-v1 subset)",
    ),
    n_draws: int = typer.Option(
        3, "--n-draws",
        help="Draws per item for --mode variance (default 3 per spec §3.4)",
    ),
    latency_item: str = typer.Option(
        "S01", "--latency-item",
        help="Which corpus item's text for --mode latency (default S01)",
    ),
    trials: int = typer.Option(
        50, "--trials",
        help="Serial trials per provider for --mode latency (default 50)",
    ),
    spend_cap: float | None = typer.Option(
        None, "--spend-cap",
        help="USD cap for this run (overrides VEVAL_SPEND_CAP_USD env var; default $100)",
    ),
    no_spend_cap: bool = typer.Option(
        False, "--no-spend-cap",
        help="Disable spend cap entirely (default: cap enforced)",
    ),
    pricing_file: Path = typer.Option(
        Path("configs/pricing.yaml"), "--pricing-file",
    ),
) -> None:
    """Run the campaign: adapter.synthesize() across (provider, use_case, item)."""
    try:
        parsed_mode = RunMode(mode)
    except ValueError:
        console.print(f"[red]--mode must be campaign|variance|latency, got: {mode}[/red]")
        raise typer.Exit(code=2) from None

    if use_case:
        for uc in use_case:
            if uc not in ("conversational", "narration"):
                console.print(f"[red]--use-case must be conversational|narration, got: {uc}[/red]")
                raise typer.Exit(code=2)

    cache: SynthesisCache | None
    if no_cache or parsed_mode != RunMode.campaign:
        # Variance/latency modes MUST skip the cache (fresh calls are the
        # measurement); campaign mode uses cache unless --no-cache.
        cache = None
    else:
        cache = SynthesisCache(cache_dir=cache_dir)

    # Spend tracker
    tracker: SpendTracker | None
    if no_spend_cap:
        tracker = None
    else:
        pricing = load_pricing(pricing_file)
        tracker = SpendTracker.from_env(pricing=pricing, cap_usd_override=spend_cap)

    runner = Runner(
        providers_file=providers_file,
        voices_file=voices_file,
        corpus_dir=corpus_dir,
        pricing_file=pricing_file,
        cache=cache,
        spend_tracker=tracker,
    )

    console.rule(f"[bold]veval generate --mode {parsed_mode.value}[/bold]")
    if items:
        console.print(f"[yellow]Pilot / restricted item set: {items}[/yellow]")
    if provider:
        console.print(f"[yellow]Restricted providers: {provider}[/yellow]")
    if use_case:
        console.print(f"[yellow]Restricted use cases: {use_case}[/yellow]")
    if cache is not None:
        stats = cache.stats()
        console.print(f"[dim]Cache: {cache_dir} ({stats['entries']} entries, {stats['total_bytes']:,} bytes)[/dim]")
    else:
        console.print("[dim]Cache: disabled[/dim]")
    if tracker is not None:
        console.print(f"[dim]Spend cap: ${tracker.cap_usd:.2f}[/dim]")
    else:
        console.print("[dim]Spend cap: disabled (--no-spend-cap)[/dim]")
    console.print()

    if parsed_mode == RunMode.campaign:
        summary = runner.run_campaign(
            use_cases=use_case,  # type: ignore[arg-type]
            provider_names=provider,
            item_ids=items,
        )
    elif parsed_mode == RunMode.variance:
        if items:
            console.print("[yellow]--items ignored for variance mode; using variance_subset.yaml[/yellow]")
        summary = runner.run_variance(
            use_cases=use_case,  # type: ignore[arg-type]
            provider_names=provider,
            variance_subset_file=variance_subset_file,
            n_draws=n_draws,
        )
    else:  # latency
        # Latency mode uses a single use case + single item (spec §D1).
        # If the caller passed multiple use cases, take the first; if none,
        # default to conversational.
        latency_use_case = (use_case[0] if use_case else "conversational")
        if use_case and len(use_case) > 1:
            console.print(
                f"[yellow]--mode latency takes one use case; using '{latency_use_case}'[/yellow]"
            )
        if items:
            console.print("[yellow]--items ignored for latency mode; use --latency-item[/yellow]")
        summary = runner.run_latency(
            provider_names=provider,
            use_case=latency_use_case,  # type: ignore[arg-type]
            item_id=latency_item,
            trials=trials,
        )

    _print_generate_summary(summary)
    if tracker is not None:
        console.print()
        spend_table = Table(title="Estimated spend (USD)", show_header=True)
        spend_table.add_column("Provider", style="bold")
        spend_table.add_column("Spend", justify="right")
        for prov, usd in sorted(tracker.per_provider_usd.items()):
            spend_table.add_row(prov, f"${usd:.4f}")
        spend_table.add_row("[bold]TOTAL[/bold]", f"[bold]${tracker.total_usd:.4f}[/bold]")
        spend_table.add_row("[dim]cap[/dim]", f"[dim]${tracker.cap_usd:.2f}[/dim]")
        console.print(spend_table)
    if summary.failed > 0:
        raise typer.Exit(code=1)


def _print_generate_summary(summary: RunSummary) -> None:
    """Compact summary table for a generate run."""
    console.print()
    console.rule(f"[bold]Summary — {summary.mode.value}[/bold]")

    header = Table(show_header=False, box=None, padding=(0, 2))
    header.add_row("run_id", summary.run_id)
    header.add_row("run_dir", str(summary.run_dir))
    header.add_row("elapsed", f"{summary.elapsed_s:.1f}s")
    header.add_row("total items", str(summary.total))
    color = "green" if summary.failed == 0 else ("yellow" if summary.ok > 0 else "red")
    header.add_row("results", f"[{color}]{summary.ok} ok · {summary.failed} failed[/{color}]")
    console.print(header)
    console.print()

    per_provider = Table(title="Per provider", show_header=True)
    per_provider.add_column("Provider", style="bold")
    per_provider.add_column("OK", justify="right", style="green")
    per_provider.add_column("Failed", justify="right", style="red")

    providers = sorted(set(summary.per_provider_ok) | set(summary.per_provider_failed))
    for prov in providers:
        ok = summary.per_provider_ok.get(prov, 0)
        failed = summary.per_provider_failed.get(prov, 0)
        per_provider.add_row(prov, str(ok), str(failed) if failed else "—")
    console.print(per_provider)


if __name__ == "__main__":
    app()
