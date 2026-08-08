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
from veval.runner import RunMode, Runner, RunSummary, SynthesisCache

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

    runner = Runner(
        providers_file=providers_file,
        voices_file=voices_file,
        corpus_dir=corpus_dir,
        cache=cache,
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
    console.print()

    if parsed_mode == RunMode.campaign:
        summary = runner.run_campaign(
            use_cases=use_case,  # type: ignore[arg-type]
            provider_names=provider,
            item_ids=items,
        )
    elif parsed_mode == RunMode.variance:
        console.print("[red]--mode variance lands in Phase D.3[/red]")
        raise typer.Exit(code=2)
    else:  # latency
        console.print("[red]--mode latency lands in Phase D.4[/red]")
        raise typer.Exit(code=2)

    _print_generate_summary(summary)
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
