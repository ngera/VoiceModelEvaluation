"""End-to-end health check. Called by `veval doctor` and the Streamlit Doctor page.

Design rule (CLAUDE.md): admin panel is a thin wrapper — no duplicate logic.
Both frontends call `run_doctor()` and render the same `DoctorReport`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from veval.adapters import ADAPTERS
from veval.adapters.base import ProviderError, SynthesisOptions, SynthesisResult
from veval.config import ProviderConfig, load_providers
from veval.store.run_store import Run, default_run_store


@dataclass
class AdapterCheck:
    provider: str
    ok: bool
    notes: str = ""
    result: SynthesisResult | None = None


@dataclass
class DoctorReport:
    configs_ok: bool
    configs_message: str
    envs_present: dict[str, bool] = field(default_factory=dict)
    adapter_results: list[AdapterCheck] = field(default_factory=list)
    run_dir: Path | None = None

    def configs_status(self) -> str:
        if self.configs_ok:
            return f"[green]✓ {self.configs_message}[/green]"
        return f"[red]✗ {self.configs_message}[/red]"

    def env_status(self) -> str:
        present = sum(1 for v in self.envs_present.values() if v)
        total = len(self.envs_present)
        color = "green" if present == total else ("yellow" if present > 0 else "red")
        return f"[{color}]{present}/{total} present[/{color}]"


def run_doctor(
    providers_file: Path = Path("configs/providers.yaml"),
    only_provider: str | None = None,
    probe_text: str = "The quick brown fox jumps over the lazy dog.",
    probe_voice: str | None = None,
) -> DoctorReport:
    """Full health check. Returns a `DoctorReport` — never raises."""

    # 1. Configs
    try:
        providers = load_providers(providers_file)
        configs_ok = True
        configs_message = f"{providers_file} — {len(providers.providers)} providers"
    except FileNotFoundError:
        return DoctorReport(
            configs_ok=False,
            configs_message=(
                f"{providers_file} not found — using registered adapters as fallback"
            ),
            envs_present={},
            adapter_results=_check_registered_adapters(only_provider, probe_text, probe_voice),
        )
    except Exception as e:  # noqa: BLE001 — doctor never raises
        return DoctorReport(
            configs_ok=False,
            configs_message=f"{providers_file} — parse error: {e}",
            envs_present={},
            adapter_results=[],
        )

    # 2. Env vars
    envs_present: dict[str, bool] = {}
    selected: list[ProviderConfig] = []
    for p in providers.providers:
        envs_present[p.env_key] = bool(os.environ.get(p.env_key))
        if only_provider is None or p.name == only_provider:
            selected.append(p)

    if only_provider and not selected:
        return DoctorReport(
            configs_ok=configs_ok,
            configs_message=configs_message,
            envs_present=envs_present,
            adapter_results=[
                AdapterCheck(provider=only_provider, ok=False, notes="not in providers.yaml"),
            ],
        )

    # 3. Adapter smoke tests
    run = default_run_store().new_run(kind="doctor", extras={
        "probe_text": probe_text,
        "probe_voice": probe_voice,
        "providers_file": str(providers_file),
    })
    adapter_results = [_probe_adapter(p, probe_text, probe_voice, run) for p in selected]
    run.finalize()

    return DoctorReport(
        configs_ok=configs_ok,
        configs_message=configs_message,
        envs_present=envs_present,
        adapter_results=adapter_results,
        run_dir=run.dir,
    )


def _probe_adapter(
    p: ProviderConfig,
    text: str,
    voice_override: str | None,
    run: Run,
) -> AdapterCheck:
    adapter_cls = ADAPTERS.get(p.name)
    if adapter_cls is None:
        return AdapterCheck(
            provider=p.name, ok=False, notes=f"no adapter class registered for `{p.name}`"
        )

    api_key = os.environ.get(p.env_key)
    if not api_key:
        return AdapterCheck(provider=p.name, ok=False, notes=f"env var {p.env_key} not set")

    try:
        adapter = adapter_cls(api_key=api_key, model=p.model, endpoint=p.endpoint)
    except Exception as e:  # noqa: BLE001
        return AdapterCheck(provider=p.name, ok=False, notes=f"adapter init failed: {e}")

    voice_id = voice_override or p.model  # doctor probe uses model string as voice if none given
    opts = SynthesisOptions(text=text, voice_id=voice_id, output_format="wav", streaming=True)

    try:
        result = adapter.synthesize(opts)
    except ProviderError as e:
        run.log_api({
            "provider": p.name,
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "status_code": e.status_code,
            "retryable": e.retryable,
        })
        return AdapterCheck(provider=p.name, ok=False, notes=f"{type(e).__name__}: {e}")
    except Exception as e:  # noqa: BLE001
        run.log_api({
            "provider": p.name,
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
        })
        return AdapterCheck(provider=p.name, ok=False, notes=f"unexpected: {type(e).__name__}: {e}")

    # Write audio and log the successful call
    audio_path = run.write_audio(p.name, "probe", result.audio_bytes, ext=result.audio_format)
    run.log_api({
        "provider": p.name,
        "status": "ok",
        "ttfa_ms": result.ttfa_ms,
        "total_ms": result.total_ms,
        "chars_billed": result.chars_billed,
        "audio_bytes": len(result.audio_bytes),
        "audio_path": str(audio_path.relative_to(run.dir)),
        "meta": result.meta,
    })
    return AdapterCheck(
        provider=p.name,
        ok=True,
        result=result,
        notes=result.meta.get("request_id", "") or "",
    )


def _check_registered_adapters(
    only_provider: str | None,
    text: str,
    voice_override: str | None,
) -> list[AdapterCheck]:
    """Fallback path when providers.yaml is missing: probe any adapter that has an env key.

    Used in Phase A before Phase B has written providers.yaml.
    """
    checks: list[AdapterCheck] = []
    for name, cls in ADAPTERS.items():
        if only_provider and name != only_provider:
            continue
        # Guess env key from adapter name
        env_key = f"{name.upper()}_API_KEY"
        api_key = os.environ.get(env_key)
        if not api_key:
            checks.append(AdapterCheck(
                provider=name, ok=False,
                notes=f"providers.yaml missing; env var {env_key} not set either",
            ))
            continue
        # Best-effort probe with a placeholder model
        try:
            adapter = cls(api_key=api_key, model="aura-2-thalia-en" if name == "deepgram" else "")
            result = adapter.synthesize(SynthesisOptions(
                text=text,
                voice_id=voice_override or "aura-2-thalia-en",
                streaming=True,
            ))
            checks.append(
                AdapterCheck(provider=name, ok=True, result=result, notes="fallback probe")
            )
        except Exception as e:  # noqa: BLE001
            checks.append(
                AdapterCheck(provider=name, ok=False, notes=f"fallback probe failed: {e}")
            )
    return checks
