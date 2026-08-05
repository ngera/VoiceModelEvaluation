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
    text: str = typer.Option(
        "The quick brown fox jumps over the lazy dog.",
        "--text",
        help="Probe text for the smoke test",
    ),
    voice_id: str | None = typer.Option(
        None, "--voice",
        help="Override voice id for the probe (falls back to provider model string)",
    ),
) -> None:
    """Health-check the pipeline end-to-end BEFORE spending money on a campaign.

    Verifies configs load, API keys are present, adapters can synthesize,
    and the run store writes correctly. Same spirit as `brew doctor` or
    `flutter doctor`.
    """
    results = run_doctor(
        providers_file=providers_file,
        only_provider=provider,
        probe_text=text,
        probe_voice=voice_id,
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


if __name__ == "__main__":
    app()
