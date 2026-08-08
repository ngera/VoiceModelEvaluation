"""End-to-end health check. Called by `veval doctor` and the Streamlit Doctor page.

Design rule (CLAUDE.md): admin panel is a thin wrapper — no duplicate logic.
Both frontends call `run_doctor()` and render the same `DoctorReport`.

v2 change (post-defect 3.37): model string moved from providers.yaml to
voices.yaml. Doctor now looks up the (voice_id, model) pair for a given
(provider, use_case) — the same lookup the runner will use. For split-model
providers (Fish free vs paid), the probe uses `quality_model` to avoid
burning paid credits on a smoke test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from veval.adapters import ADAPTERS
from veval.adapters.base import ProviderError, SynthesisOptions, SynthesisResult
from veval.config import (
    ProviderConfig,
    UseCase,
    VoiceSelection,
    VoicesFile,
    load_providers,
    load_voices,
)
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


def _model_for_probe(voice: VoiceSelection) -> str:
    """Choose which model string to pass for a smoke-test probe.

    Split-model providers (currently just Fish) declare BOTH a latency model
    and a `quality_model` — the free tier for Fish. Doctor probes are smoke
    tests; use the free tier where available so probes are $0.
    """
    if voice.split_model_from_quality and voice.quality_model:
        return voice.quality_model
    return voice.model


def run_doctor(
    providers_file: Path = Path("configs/providers.yaml"),
    voices_file: Path = Path("configs/voices.yaml"),
    only_provider: str | None = None,
    use_case: UseCase = "conversational",
    probe_text: str = "The quick brown fox jumps over the lazy dog.",
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
            adapter_results=_check_registered_adapters(only_provider, probe_text),
        )
    except Exception as e:  # noqa: BLE001 — doctor never raises
        return DoctorReport(
            configs_ok=False,
            configs_message=f"{providers_file} — parse error: {e}",
            envs_present={},
            adapter_results=[],
        )

    # 1b. voices.yaml — model + voice_id per (provider, use_case) live here since defect 3.37
    voices: VoicesFile | None = None
    voices_note = ""
    try:
        voices = load_voices(voices_file)
        voices_note = f" · voices.yaml ({len(voices.voices)} locks)"
    except FileNotFoundError:
        voices_note = f" · voices.yaml missing — probes will skip"
    except Exception as e:  # noqa: BLE001
        voices_note = f" · voices.yaml parse error: {e}"

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
            configs_message=configs_message + voices_note,
            envs_present=envs_present,
            adapter_results=[
                AdapterCheck(provider=only_provider, ok=False, notes="not in providers.yaml"),
            ],
        )

    # 3. Adapter smoke tests
    run = default_run_store().new_run(kind="doctor", extras={
        "probe_text": probe_text,
        "use_case": use_case,
        "providers_file": str(providers_file),
        "voices_file": str(voices_file),
    })
    adapter_results = [_probe_adapter(p, voices, use_case, probe_text, run) for p in selected]
    run.finalize()

    return DoctorReport(
        configs_ok=configs_ok,
        configs_message=configs_message + voices_note,
        envs_present=envs_present,
        adapter_results=adapter_results,
        run_dir=run.dir,
    )


def _probe_adapter(
    p: ProviderConfig,
    voices: VoicesFile | None,
    use_case: UseCase,
    text: str,
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

    if voices is None:
        return AdapterCheck(
            provider=p.name, ok=False,
            notes="voices.yaml missing; cannot resolve (voice_id, model) for probe",
        )

    try:
        voice = voices.get(p.name, use_case)
    except KeyError:
        return AdapterCheck(
            provider=p.name, ok=False,
            notes=f"no voices.yaml entry for {p.name} × {use_case}",
        )

    model = _model_for_probe(voice)

    try:
        adapter = adapter_cls(
            api_key=api_key, model=model, endpoint=p.endpoint, version=p.version,
        )
    except Exception as e:  # noqa: BLE001
        return AdapterCheck(provider=p.name, ok=False, notes=f"adapter init failed: {e}")

    opts = SynthesisOptions(
        text=text, voice_id=voice.voice_id, output_format="wav", streaming=True,
    )

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
        "billing_unit": result.billing_unit,
        "audio_bytes": len(result.audio_bytes),
        "audio_path": str(audio_path.relative_to(run.dir)),
        "voice_id": voice.voice_id,
        "model": model,
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
) -> list[AdapterCheck]:
    """Fallback path when providers.yaml is missing: probe any adapter that has an env key.

    Used pre-Phase-B, before providers.yaml has been written. Hardcodes a
    Deepgram default so the walking skeleton still demonstrates the flow.
    """
    checks: list[AdapterCheck] = []
    for name, cls in ADAPTERS.items():
        if only_provider and name != only_provider:
            continue
        env_key = f"{name.upper()}_API_KEY"
        api_key = os.environ.get(env_key)
        if not api_key:
            checks.append(AdapterCheck(
                provider=name, ok=False,
                notes=f"providers.yaml missing; env var {env_key} not set either",
            ))
            continue
        try:
            adapter = cls(api_key=api_key, model="aura-2-thalia-en" if name == "deepgram" else "")
            result = adapter.synthesize(SynthesisOptions(
                text=text,
                voice_id="aura-2-thalia-en",
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
