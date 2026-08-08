"""veval CLI entry point.

Subcommands (implemented incrementally per Phase in CLAUDE.md):
- doctor    (Phase A) — smoke-test all/one adapter end-to-end
- generate  (Phase D) — run the corpus × providers campaign
- analyze   (Phase E) — WER + quality + hygiene + latency + variance + drift + cost
- rate      (Phase F) — build rating manifest, normalize audio, fit Bradley-Terry
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
from veval.config import load_pricing
from veval.doctor import DoctorReport, run_doctor
from veval.runner import RunMode, Runner, RunSummary, SpendTracker, SynthesisCache

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


rate_app = typer.Typer(name="rate", help="Phase F — human A/B rating pipeline.", no_args_is_help=True)
app.add_typer(rate_app, name="rate")


@rate_app.command("build")
def rate_build(
    rater: str = typer.Option(..., "--rater", help="Rater id (per-rater manifest seed)"),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Campaign run id to source audio from (default: latest campaign)",
    ),
    use_case: list[str] = typer.Option(
        ["conversational", "narration"], "--use-case", "-u",
        help="Which use cases to include",
    ),
    providers_file: Path = typer.Option(Path("configs/providers.yaml"), "--providers-file"),
    corpus_dir: Path = typer.Option(Path("corpus"), "--corpus-dir"),
    audio_root: Path = typer.Option(
        Path("rating/audio"), "--audio-root",
        help="Where normalized audio lives (relative to rating/index.html)",
    ),
    manifest_out: Path = typer.Option(
        Path("rating/manifest.json"), "--manifest-out",
    ),
    reps: int = typer.Option(
        3, "--reps",
        help="Repetitions per pair (default 3 per D-009; original spec was 5)",
    ),
    consistency_fraction: float = typer.Option(
        0.10, "--consistency-fraction",
        help="Fraction of judgments repeated later for consistency check",
    ),
    session_size: int = typer.Option(40, "--session-size"),
    items: list[str] | None = typer.Option(
        None, "--items", "-i",
        help=(
            "Restrict pair selection to these corpus items (e.g. --items S01 "
            "--items M01). Match the item set of your source run so no "
            "pair schedules missing audio."
        ),
    ),
    exclude_system: list[str] | None = typer.Option(
        None, "--exclude-system",
        help=(
            "Drop these systems from pair enumeration (e.g. --exclude-system "
            "orpheus if Replicate credits are exhausted). Applied AFTER the "
            "providers.yaml lookup so pair count drops accordingly."
        ),
    ),
) -> None:
    """Build the per-rater rating manifest.

    Sources the anchor + 8 providers from providers.yaml and the corpus
    from corpus_dir. Writes `rating/manifest.json`. The static rating
    page (`rating/index.html`) loads this on boot.
    """
    from veval.config import load_corpus, load_providers
    from veval.human.pair_builder import ANCHOR_SYSTEM, build_manifest, write_manifest
    from veval.store.run_store import default_run_store

    providers = load_providers(providers_file)
    systems = [p.name for p in providers.providers] + [ANCHOR_SYSTEM]
    if exclude_system:
        systems = [s for s in systems if s not in set(exclude_system)]

    corpora: dict[str, object] = {}
    for uc in use_case:
        if uc not in ("conversational", "narration"):
            console.print(f"[red]--use-case must be conversational|narration, got: {uc}[/red]")
            raise typer.Exit(code=2)
        corpora[uc] = load_corpus(corpus_dir / f"{uc}.yaml")

    # Source run for context (not strictly needed by build_manifest;
    # useful in the printed summary + as a fixture for downstream normalize)
    if run_id is None:
        runs = default_run_store().list_runs("campaign")
        if not runs:
            console.print("[red]no campaign runs under ./runs/ — generate first[/red]")
            raise typer.Exit(code=2)
        run_dir = runs[0]
    else:
        run_dir = Path("runs") / run_id
    if not run_dir.exists():
        console.print(f"[red]run dir not found: {run_dir}[/red]")
        raise typer.Exit(code=2)

    manifest = build_manifest(
        rater_id=rater,
        systems=systems,
        use_cases=use_case,  # type: ignore[arg-type]
        corpora=corpora,  # type: ignore[arg-type]
        audio_root=audio_root,
        reps_per_pair=reps,
        session_size=session_size,
        consistency_repeat_fraction=consistency_fraction,
        restrict_to_items=set(items) if items else None,
    )
    write_manifest(manifest, manifest_out)

    console.rule(f"[bold]rate build[/bold] --rater {rater}")
    console.print(f"source run  : {run_dir}")
    console.print(f"systems     : {len(manifest.systems)}  ({', '.join(manifest.systems)})")
    console.print(f"pairs       : {len(manifest.systems) * (len(manifest.systems) - 1) // 2}")
    console.print(f"judgments   : {manifest.total_judgments}")
    console.print(f"sessions    : {manifest.total_sessions} (~{session_size} judgments each)")
    console.print(f"manifest -> {manifest_out}")
    console.print()
    console.print(
        "[dim]next: `veval rate normalize --source-run <run_id>` "
        "then `veval rate serve`[/dim]"
    )


@rate_app.command("normalize")
def rate_normalize(
    source_run: str | None = typer.Option(
        None,
        "--source-run",
        help="Run id under ./runs to normalize from (default: latest campaign)",
    ),
    audio_root: Path = typer.Option(Path("rating/audio"), "--audio-root"),
    target_lufs: float = typer.Option(
        -18.0, "--target-lufs",
        help="Target integrated loudness (spec §D4: -18)",
    ),
    anchor_dir: Path | None = typer.Option(
        None, "--anchor-dir",
        help=(
            "Directory of anchor WAVs named {use_case}_{item_id}.wav. "
            "Copied + normalized alongside the provider audio."
        ),
    ),
) -> None:
    """Normalize every provider WAV in a campaign run to -18 LUFS and
    copy it to `rating/audio/{use_case}/{system}/{item_id}.wav`.

    -18 LUFS is mandatory before rating (spec §D4 line 393) — without
    it, louder clips systematically win A/B and the test measures gain
    staging, not voice quality.
    """
    from veval.analyze.common import RunReader
    from veval.human.loudness import normalize_file
    from veval.store.run_store import default_run_store

    if source_run is None:
        runs = default_run_store().list_runs("campaign")
        if not runs:
            console.print("[red]no campaign runs under ./runs/[/red]")
            raise typer.Exit(code=2)
        run_dir = runs[0]
    else:
        run_dir = Path("runs") / source_run

    reader = RunReader(run_dir)
    ok = 0
    failed = 0
    console.rule(f"[bold]rate normalize[/bold] from {run_dir.name}")
    for rec in reader.records():
        dst = audio_root / rec.use_case / rec.provider / f"{rec.item_id}.wav"
        r = normalize_file(rec.wav_path, dst, target_lufs=target_lufs)
        if r.error:
            failed += 1
            console.print(f"  [red]FAIL[/red] {rec.provider}/{rec.use_case}/{rec.item_id}: {r.error}")
        else:
            ok += 1

    if anchor_dir and anchor_dir.exists():
        console.print(f"[dim]anchor: normalizing WAVs under {anchor_dir}[/dim]")
        for wav in anchor_dir.rglob("*.wav"):
            stem = wav.stem  # {use_case}_{item_id}
            if "_" not in stem:
                console.print(f"  [yellow]skip {wav.name} (expected use_case_item_id.wav)[/yellow]")
                continue
            uc, item_id = stem.split("_", 1)
            dst = audio_root / uc / "anchor" / f"{item_id}.wav"
            r = normalize_file(wav, dst, target_lufs=target_lufs)
            if r.error:
                failed += 1
            else:
                ok += 1

    console.print()
    console.print(f"normalized {ok} files -> {audio_root}   ({failed} failed)")


@rate_app.command("serve")
def rate_serve(
    port: int = typer.Option(8080, "--port"),
    rating_dir: Path = typer.Option(Path("rating"), "--rating-dir"),
) -> None:
    """Serve the static rating page over localhost.

    Browsers block `fetch()` on `file://` URLs; the rating page needs
    HTTP. Uses Python's built-in HTTP server — no external dependency.
    Open http://localhost:<port> once it starts.
    """
    import http.server
    import socketserver
    import webbrowser

    if not (rating_dir / "index.html").exists():
        console.print(f"[red]{rating_dir}/index.html not found[/red]")
        raise typer.Exit(code=2)
    if not (rating_dir / "manifest.json").exists():
        console.print(
            f"[yellow]warning: {rating_dir}/manifest.json missing "
            "- the page will show a build hint.[/yellow]"
        )

    # Subclass to silence the very common ConnectionResetError /
    # BrokenPipeError that fires when a browser aborts an in-flight
    # audio download (user paused, seeked, or moved to the next
    # judgment mid-transfer). Stock SimpleHTTPRequestHandler dumps a
    # 20-line traceback to stderr each time; the errors are harmless
    # and would only distract the rater.
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def handle_one_request(self) -> None:
            try:
                super().handle_one_request()
            except (ConnectionResetError, BrokenPipeError):
                pass

        def log_message(self, format: str, *args: object) -> None:
            # Suppress the per-request access log so the console stays
            # readable during a rating session. Errors still print.
            return

    # SimpleHTTPRequestHandler serves from CWD; chdir first
    import os
    os.chdir(rating_dir)

    with socketserver.TCPServer(("", port), QuietHandler) as httpd:
        url = f"http://localhost:{port}"
        console.rule("[bold]rate serve[/bold]")
        console.print(f"serving {rating_dir.resolve()} at [bold]{url}[/bold]")
        console.print("[dim]Ctrl-C to stop[/dim]")
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\nstopped.")


@rate_app.command("fit")
def rate_fit(
    judgments_csv: Path = typer.Argument(..., help="CSV downloaded from the rating page"),
    n_resamples: int = typer.Option(2000, "--n-resamples"),
    alpha: float = typer.Option(0.5, "--alpha", help="L2 penalty (analyzers.yaml)"),
    out: Path = typer.Option(
        Path("analysis/bt_fit.json"), "--out",
        help="Where to write the fit + CIs",
    ),
) -> None:
    """Bradley-Terry fit + clustered-bootstrap CIs from a judgments CSV.

    One fit per use case (spec §4.3). Domination is asserted only when
    the pairwise-difference CI excludes zero (spec §5 line 532).
    """
    import csv as csvmod
    import json

    from veval.human.bt import (
        RawJudgment,
        consistency_rate,
        fit_per_use_case,
    )

    if not judgments_csv.exists():
        console.print(f"[red]not found: {judgments_csv}[/red]")
        raise typer.Exit(code=2)

    judgments: list[RawJudgment] = []
    with judgments_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csvmod.DictReader(f):
            judgments.append(RawJudgment(
                use_case=row["use_case"],
                item_id=row["item_id"],
                system_left=row["system_left"],
                system_right=row["system_right"],
                winner=row["winner"],  # type: ignore[arg-type]
                is_consistency_repeat=row["is_consistency_repeat"].lower() == "true",
            ))

    consistency, n_repeats = consistency_rate(judgments)
    console.rule("[bold]rate fit[/bold]")
    console.print(f"loaded {len(judgments)} judgments from {judgments_csv}")
    console.print(f"consistency: {consistency:.2%}  (n={n_repeats} repeats)")

    fits = fit_per_use_case(judgments, n_resamples=n_resamples, alpha=alpha)

    payload = {
        "source": str(judgments_csv),
        "n_judgments": len(judgments),
        "consistency_rate": consistency,
        "n_consistency_repeats": n_repeats,
        "n_resamples": n_resamples,
        "alpha": alpha,
        "fits": {
            uc: {
                "systems": f.systems,
                "strengths": f.strengths,
                "strength_ci_lower": f.strength_ci_lower,
                "strength_ci_upper": f.strength_ci_upper,
                "pairwise_diff": {f"{a}__{b}": v for (a, b), v in f.pairwise_diff.items()},
                "n_judgments": f.n_judgments,
                "n_items": f.n_items,
            }
            for uc, f in fits.items()
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    console.print()
    for uc, f in fits.items():
        console.print(f"[bold]{uc}[/bold] (n={f.n_judgments} judgments, {f.n_items} items)")
        for sys_name, strength in sorted(
            zip(f.systems, f.strengths, strict=True), key=lambda x: -x[1]
        ):
            lo = f.strength_ci_lower[sys_name]
            hi = f.strength_ci_upper[sys_name]
            console.print(f"  {sys_name:12s} {strength:+.2f}  CI [{lo:+.2f}, {hi:+.2f}]")
    console.print()
    console.print(f"written to {out}")


@app.command()
def score(
    run_id: str | None = typer.Argument(
        None,
        help="Analysis directory under ./analysis (default: latest by mtime)",
    ),
    bt_fit_path: Path = typer.Option(
        Path("analysis/bt_fit.json"), "--bt-fit",
        help="Bradley-Terry fit JSON from `veval rate fit`",
    ),
    cost_axis_projection: str = typer.Option(
        "100K_words_per_month", "--cost-projection",
        help="Which cost_model column to use for the cost axis",
    ),
    gates_file: Path = typer.Option(Path("configs/gates.yaml"), "--gates-file"),
    hi_snapshot: Path | None = typer.Option(
        None, "--hi-snapshot",
        help="Optional Humanness Index snapshot JSON (skips HI comparison if omitted)",
    ),
    out: Path = typer.Option(
        Path("analysis/score.json"), "--out",
        help="Where to write the combined score payload",
    ),
) -> None:
    """Phase G scoring: gates -> survivors -> frontiers with CI domination
    -> robustness sweep -> HI reproduces column -> Spearman rho.
    """
    from veval.config import load_analyzers, load_gates
    from veval.human.bt import BTFit
    from veval.score import correlations, frontier, gates as gates_mod, hi_loader, robustness
    from veval.store.run_store import default_run_store

    # Discover latest analysis dir if not provided
    if run_id is None:
        runs = default_run_store().list_runs("campaign")
        if not runs:
            console.print("[red]no campaign runs under ./runs/[/red]")
            raise typer.Exit(code=2)
        analysis_dir = Path("analysis") / runs[0].name
    else:
        analysis_dir = Path("analysis") / run_id
    if not analysis_dir.exists():
        console.print(f"[red]analysis dir not found: {analysis_dir}[/red]")
        raise typer.Exit(code=2)

    console.rule(f"[bold]veval score[/bold] {analysis_dir.name}")

    analyses = gates_mod.load_analyses(analysis_dir)
    console.print(f"loaded {len(analyses)} analyzer output(s): {sorted(analyses)}")

    gates = load_gates(gates_file)
    # Provider set: union across analyzer outputs
    providers: set[str] = set()
    for payload in analyses.values():
        for row in payload.get("by_provider", []):
            if "provider" in row:
                providers.add(row["provider"])
    provider_list = sorted(providers)
    console.print(f"providers: {provider_list}")

    # --- Gates ---
    console.print("[bold]gates[/bold] - apply per-use-case, honor na_policy")
    survivals = gates_mod.apply_gates(provider_list, gates, analyses)
    survivors_by_uc: dict[str, list[str]] = {}
    exempt_by_provider: dict[str, dict[str, list[str]]] = {}
    for s in survivals:
        survivors_by_uc.setdefault(s.use_case, [])
        exempt_by_provider.setdefault(s.use_case, {}).setdefault(s.provider, [])
        if s.survives:
            survivors_by_uc[s.use_case].append(s.provider)
        exempt_by_provider[s.use_case][s.provider].extend(s.exempt_gates)
    for uc, sv in survivors_by_uc.items():
        console.print(f"  {uc}: {len(sv)} survivor(s) - {sv}")

    # --- Robustness ---
    console.print("[bold]robustness[/bold] - sweep gates over their robustness_points")
    robustness_results = robustness.sweep_all(provider_list, gates, analyses)
    for r in robustness_results:
        flag = "stable" if r.is_stable else "UNSTABLE"
        console.print(f"  {r.use_case}.{r.gate_metric}: {flag} across {r.robustness_points}")

    # --- BT + frontiers ---
    frontiers: dict[str, dict[str, Any]] = {}
    bt_data = None
    if bt_fit_path.exists():
        import json
        bt_data = json.loads(bt_fit_path.read_text(encoding="utf-8"))
        console.print(f"[bold]frontiers[/bold] - Pareto + CI domination from {bt_fit_path}")
        cost_payload = analyses.get("cost_model.json")
        latency_payload = analyses.get("latency.json")
        for uc_name, fit_data in bt_data.get("fits", {}).items():
            # Reconstruct a BTFit-shaped object with pairwise_diff intact
            pairwise = {}
            for key, d in fit_data.get("pairwise_diff", {}).items():
                a, b = key.split("__")
                pairwise[(a, b)] = d
            bt_fit = BTFit(
                use_case=uc_name,
                systems=fit_data["systems"],
                strengths=fit_data["strengths"],
                strength_ci_lower=fit_data.get("strength_ci_lower", {}),
                strength_ci_upper=fit_data.get("strength_ci_upper", {}),
                pairwise_diff=pairwise,
                n_judgments=fit_data.get("n_judgments", 0),
                n_items=fit_data.get("n_items", 0),
            )
            survivors = survivors_by_uc.get(uc_name, [])
            exempts = exempt_by_provider.get(uc_name, {})
            frontiers[uc_name] = {}
            for axis_name in ("cost", "latency"):
                fr = frontier.build_frontier(
                    bt_fit, survivors=survivors, axis=axis_name,
                    cost_payload=cost_payload if axis_name == "cost" else None,
                    latency_payload=latency_payload if axis_name == "latency" else None,
                    cost_projection=cost_axis_projection,
                    exempt_providers=exempts,
                )
                frontiers[uc_name][axis_name] = frontier.as_dict(fr)
                on = [p.provider for p in fr.points if p.on_frontier]
                console.print(f"  {uc_name}.{axis_name} frontier: {on}")
    else:
        console.print(f"[yellow]no BT fit at {bt_fit_path} - skipping frontiers[/yellow]")

    # --- HI comparison ---
    hi_output: dict[str, Any] | None = None
    if hi_snapshot and hi_snapshot.exists() and bt_data:
        console.print("[bold]HI[/bold] - Humanness Index reproduces column")
        snap = hi_loader.load_snapshot(hi_snapshot)
        # Conventionally compare against the conversational use case
        conv_fit = bt_data.get("fits", {}).get("conversational")
        if conv_fit:
            strengths = dict(zip(conv_fit["systems"], conv_fit["strengths"]))
            comparisons = hi_loader.compare(snap, strengths)
            hi_output = {
                "snapshot": {"captured_at": snap.captured_at, "source": snap.source},
                "comparisons": hi_loader.as_dicts(comparisons),
            }
    elif hi_snapshot and not hi_snapshot.exists():
        console.print(f"[yellow]HI snapshot not found: {hi_snapshot}[/yellow]")

    # --- Spearman correlations ---
    correlations_out: list[dict[str, Any]] = []
    if bt_data:
        console.print("[bold]correlations[/bold] - Spearman rho")
        conv_fit = bt_data.get("fits", {}).get("conversational")
        if conv_fit:
            d4 = dict(zip(conv_fit["systems"], conv_fit["strengths"]))
            # D3 (TTSDS2) - convention: use audiobox PQ mean when TTSDS2
            # per-provider score isn't available (Phase E quality.py note).
            quality_payload = analyses.get("quality.json")
            if quality_payload:
                d3 = {
                    r["provider"]: r["audiobox_means"].get("production_quality")
                    for r in quality_payload.get("audiobox_by_provider", [])
                    if r["use_case"] == "conversational"
                    and r["audiobox_means"].get("production_quality") is not None
                }
                if d3:
                    r = correlations.spearman(
                        d3, d4, left_axis="D3_PQ", right_axis="D4_BT",
                    )
                    correlations_out.append(correlations.as_dict(r))
                    console.print(f"  D3 <-> D4: rho={r.rho} n={r.n_shared} ({r.interpretation})")
            if hi_output:
                hi_scores = {
                    p: c["hi_score"]
                    for p, c in hi_output["comparisons"].items()
                    if c["hi_score"] is not None
                }
                if hi_scores:
                    r_d4_hi = correlations.spearman(
                        d4, hi_scores, left_axis="D4_BT", right_axis="HI",
                    )
                    correlations_out.append(correlations.as_dict(r_d4_hi))
                    console.print(
                        f"  D4 <-> HI: rho={r_d4_hi.rho} n={r_d4_hi.n_shared} "
                        f"({r_d4_hi.interpretation})"
                    )

    # --- Write score.json ---
    payload = {
        "analysis_dir": str(analysis_dir),
        "bt_fit_source": str(bt_fit_path) if bt_data else None,
        "hi_snapshot_source": str(hi_snapshot) if hi_output else None,
        "survivals": gates_mod.as_dicts(survivals),
        "robustness": robustness.as_dicts(robustness_results),
        "frontiers": frontiers,
        "hi": hi_output,
        "correlations": correlations_out,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    import json
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    console.print()
    console.rule("[bold green]score complete[/bold green]")
    console.print(f"written to {out}")


@app.command()
def report(
    score_json: Path = typer.Argument(
        Path("analysis/score.json"),
        help="Path to score.json produced by `veval score`",
    ),
    out_dir: Path = typer.Option(
        Path("site"), "--out",
        help="Where to write memos + charts + case study markdown",
    ),
) -> None:
    """Render tables + Altair PNGs + interactive Plotly HTML from
    `score.json`. Case study + per-use-case memos land in `site/`.
    """
    import json
    from veval.report.charts import (
        altair_frontier, altair_to_png,
        plotly_frontier, plotly_to_html,
    )
    from veval.report.memos import case_study_markdown, memo_markdown

    if not score_json.exists():
        console.print(f"[red]score.json not found: {score_json}[/red]")
        console.print("[dim]run `veval score` first[/dim]")
        raise typer.Exit(code=2)

    score = json.loads(score_json.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "interactive").mkdir(exist_ok=True)

    console.rule(f"[bold]veval report[/bold] from {score_json}")

    # --- Memos ---
    for uc in ("conversational", "narration"):
        memo_path = out_dir / f"memo_{uc}.md"
        memo_path.write_text(memo_markdown(score, uc), encoding="utf-8")
        console.print(f"  wrote {memo_path}")

    # --- Case study ---
    cs_path = out_dir / "case_study.md"
    cs_path.write_text(case_study_markdown(score), encoding="utf-8")
    console.print(f"  wrote {cs_path}")

    # --- Charts (per use case, per axis) ---
    for uc in ("conversational", "narration"):
        for axis in ("cost", "latency"):
            frontier_payload = (
                score.get("frontiers", {}).get(uc, {}).get(axis)
            )
            if not frontier_payload or not frontier_payload.get("points"):
                console.print(
                    f"  [dim]skip {uc}.{axis} chart (no frontier data)[/dim]"
                )
                continue
            png_path = out_dir / f"{uc}_{axis}.png"
            html_path = out_dir / "interactive" / f"{uc}_{axis}.html"
            altair_to_png(altair_frontier(frontier_payload), png_path)
            plotly_to_html(plotly_frontier(frontier_payload), html_path)
            console.print(f"  wrote {png_path} + {html_path}")

    console.print()
    console.rule("[bold green]report complete[/bold green]")
    console.print(f"outputs in {out_dir}")


if __name__ == "__main__":
    app()
