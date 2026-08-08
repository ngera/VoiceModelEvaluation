"""veval CLI entry point.

Subcommands (implemented incrementally per Phase in CLAUDE.md):
- doctor    (Phase A) — smoke-test all/one adapter end-to-end
- generate  (Phase D) — run the corpus × providers campaign
- analyze   (Phase E) — WER + quality + hygiene + latency + variance + drift + cost
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


@app.command()
def analyze(
    run_id: str | None = typer.Argument(
        None,
        help="Run id under ./runs (e.g. campaign-20260808T173545Z). Default: latest campaign.",
    ),
    stages: str = typer.Option(
        "all",
        "--stages",
        help=(
            "Comma-separated: acceptance,hygiene,latency,cost,wer,quality,"
            "variance,drift, or 'all'. Cheap stages default; wer/quality "
            "download models on first run."
        ),
    ),
    skip_ttsds: bool = typer.Option(
        False, "--skip-ttsds", help="Skip TTSDS2 inside quality stage (fast iteration)"
    ),
    skip_audiobox: bool = typer.Option(
        False, "--skip-audiobox", help="Skip Audiobox inside quality stage"
    ),
    n_split_half: int = typer.Option(
        100, "--n-split-half", help="Split-half partitions for TTSDS2 stability"
    ),
    gates_file: Path = typer.Option(Path("configs/gates.yaml"), "--gates-file"),
    analyzers_file: Path = typer.Option(
        Path("configs/analyzers.yaml"), "--analyzers-file"
    ),
    pricing_file: Path = typer.Option(Path("configs/pricing.yaml"), "--pricing-file"),
    corpus_dir: Path = typer.Option(Path("corpus"), "--corpus-dir"),
    analysis_dir: Path = typer.Option(
        Path("analysis"), "--analysis-dir",
        help="Where to write analysis/<run_id>/ outputs",
    ),
) -> None:
    """Run the Phase E analyzer chain over one run dir.

    Reads from `runs/<run_id>/` and writes JSON outputs to
    `analysis/<run_id>/`. All analyzers are pure functions of the run
    store — safe to re-run without regenerating audio.
    """
    from veval.analyze import (
        acceptance,
        cost,
        drift,
        hygiene,
        latency,
        quality,
        variance,
        wer,
    )
    from veval.analyze.common import AnalysisWriter
    from veval.config import load_analyzers, load_corpus, load_gates
    from veval.store.run_store import default_run_store

    if run_id is None:
        runs = default_run_store().list_runs("campaign")
        if not runs:
            console.print("[red]no campaign runs under ./runs/[/red]")
            raise typer.Exit(code=2)
        run_dir = runs[0]
    else:
        run_dir = Path("runs") / run_id
    if not run_dir.exists():
        console.print(f"[red]run dir not found: {run_dir}[/red]")
        raise typer.Exit(code=2)

    all_stages = ["acceptance", "hygiene", "latency", "cost", "wer", "quality", "variance", "drift"]
    requested = all_stages if stages.lower() == "all" else [s.strip() for s in stages.split(",")]
    unknown = [s for s in requested if s not in all_stages]
    if unknown:
        console.print(f"[red]unknown stages: {unknown}. Valid: {all_stages}[/red]")
        raise typer.Exit(code=2)

    writer = AnalysisWriter(run_dir.name, base_dir=analysis_dir)
    console.rule(f"[bold]veval analyze {run_dir.name}[/bold]")
    console.print(f"[dim]stages: {', '.join(requested)}[/dim]")
    console.print(f"[dim]output: {writer.dir}[/dim]")
    console.print()

    results: dict[str, dict] = {}
    gates = load_gates(gates_file)

    if "acceptance" in requested:
        console.print("[bold]acceptance[/bold] - WAV header/decoded/LUFS/VAD/chars check")
        results["acceptance"] = acceptance.run(run_dir, writer=writer)
        console.print(
            f"  gate_ok={results['acceptance']['gate_ok']} "
            f"passed={results['acceptance']['passed']}/"
            f"{results['acceptance']['total_files']}"
        )

    if "hygiene" in requested:
        console.print("[bold]hygiene[/bold] - clipping / LUFS / noise floor / pauses")
        results["hygiene"] = hygiene.run(run_dir, gates=gates, writer=writer)
        console.print(
            f"  files={results['hygiene']['total_files']} errors={results['hygiene']['n_errors']}"
        )

    if "latency" in requested:
        console.print("[bold]latency[/bold] - TTFA percentiles + RTF on long items")
        results["latency"] = latency.run(run_dir, writer=writer)
        console.print(f"  items={results['latency']['total_items']}")

    if "cost" in requested:
        console.print("[bold]cost[/bold] - pricing.yaml x char counts -> cost_model.json")
        results["cost"] = cost.run(run_dir, pricing_path=pricing_file, writer=writer)
        console.print(
            f"  observed spend: ${results['cost']['total_observed_cost_usd']:.4f}"
        )

    if "wer" in requested:
        console.print("[bold]wer[/bold] - Parakeet + faster-whisper agreement (loads models)")
        analyzers = load_analyzers(analyzers_file)
        corpus_by_use_case = {}
        for uc in ("conversational", "narration"):
            p = corpus_dir / f"{uc}.yaml"
            if p.exists():
                corpus_by_use_case[uc] = load_corpus(p)
        results["wer"] = wer.run(
            run_dir, gates=gates, analyzers=analyzers,
            corpus_by_use_case=corpus_by_use_case, writer=writer,
        )
        console.print(f"  items={len(results['wer']['items'])}")

    if "quality" in requested:
        console.print("[bold]quality[/bold] - TTSDS2 + Audiobox (heavy)")
        analyzers = load_analyzers(analyzers_file)
        results["quality"] = quality.run(
            run_dir, analyzers=analyzers,
            compute_ttsds=not skip_ttsds,
            compute_audiobox=not skip_audiobox,
            n_split_half=n_split_half, writer=writer,
        )
        console.print(
            f"  ran_ttsds={results['quality']['ran_ttsds']} "
            f"ran_audiobox={results['quality']['ran_audiobox']}"
        )

    if "variance" in requested:
        console.print("[bold]variance[/bold] - within-provider SD -> noise floor + determinism")
        wer_path = writer.dir / "wer.json"
        quality_path = writer.dir / "quality.json"
        results["variance"] = variance.run(
            run_dir, gates=gates,
            wer_analysis_path=wer_path if wer_path.exists() else None,
            quality_analysis_path=quality_path if quality_path.exists() else None,
            writer=writer,
        )
        console.print(f"  providers={len(results['variance']['by_provider'])}")

    if "drift" in requested:
        console.print("[bold]drift[/bold] - per-third analysis on long narration items")
        results["drift"] = drift.run(run_dir, gates=gates, writer=writer)
        n_flagged = sum(
            r["n_monotonic_degradation"] for r in results["drift"]["by_provider"]
        )
        console.print(f"  flagged={n_flagged}")

    console.print()
    console.rule("[bold green]analyze complete[/bold green]")
    console.print(f"outputs in {writer.dir}")


if __name__ == "__main__":
    app()
