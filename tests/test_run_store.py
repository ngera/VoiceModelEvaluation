"""Run-store invariants.

CLAUDE.md states `runs/<run_id>/` is immutable and that errors are logged as
data rather than raised. Both are conventions until something enforces them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veval.store import run_store as rs
from veval.store.run_store import RunStore


def test_new_run_creates_expected_layout(tmp_path: Path) -> None:
    run = RunStore(tmp_path).new_run(kind="doctor")

    assert run.dir.is_dir()
    assert (run.dir / "audio").is_dir()
    assert run.dir.name.startswith("doctor-")
    assert run.manifest.kind == "doctor"
    assert run.manifest.finalized_at_utc is None


def test_run_id_collision_fails_loud(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Never silently reuse a run dir — that would mutate an existing run."""
    monkeypatch.setattr(rs, "_run_id", lambda kind: "doctor-FIXED")
    store = RunStore(tmp_path)
    store.new_run(kind="doctor")

    with pytest.raises(FileExistsError):
        store.new_run(kind="doctor")


def test_write_audio_layout_and_counts(tmp_path: Path) -> None:
    run = RunStore(tmp_path).new_run()

    path = run.write_audio("deepgram", "probe", b"RIFFdata", ext="wav")

    assert path == run.dir / "audio" / "deepgram" / "probe.wav"
    assert path.read_bytes() == b"RIFFdata"
    assert run.manifest.audio_count == 1
    assert run.manifest.providers == ["deepgram"]
    assert run.manifest.items == ["probe"]


def test_repeated_provider_and_item_are_not_duplicated(tmp_path: Path) -> None:
    run = RunStore(tmp_path).new_run()
    run.write_audio("deepgram", "item1", b"a")
    run.write_audio("deepgram", "item2", b"b")
    run.write_audio("fish", "item1", b"c")

    assert run.manifest.providers == ["deepgram", "fish"]
    assert run.manifest.items == ["item1", "item2"]
    assert run.manifest.audio_count == 3


def test_log_api_appends_jsonl_with_timestamp(tmp_path: Path) -> None:
    run = RunStore(tmp_path).new_run()
    run.log_api({"provider": "deepgram", "status": "ok"})
    run.log_api({"provider": "fish", "status": "ok"})

    lines = run.api_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["provider"] == "deepgram"
    assert first["ts_utc"].endswith("Z")


def test_errors_are_logged_as_data_not_raised(tmp_path: Path) -> None:
    run = RunStore(tmp_path).new_run()
    run.log_api({"provider": "deepgram", "status": "error", "message": "HTTP 429"})

    assert run.manifest.error_count == 1
    assert json.loads(run.api_log_path.read_text().strip())["message"] == "HTTP 429"


def test_log_api_serializes_non_json_values(tmp_path: Path) -> None:
    """`default=str` must keep a stray Path/exception from killing a campaign."""
    run = RunStore(tmp_path).new_run()
    run.log_api({"status": "error", "path": Path("/tmp/x"), "exc": ValueError("boom")})

    record = json.loads(run.api_log_path.read_text().strip())
    assert record["path"] == "/tmp/x"
    assert "boom" in record["exc"]


def test_finalize_writes_manifest(tmp_path: Path) -> None:
    run = RunStore(tmp_path).new_run(kind="doctor", extras={"probe_text": "hello"})
    run.write_audio("deepgram", "probe", b"x")

    manifest_path = run.finalize()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest_path == run.dir / "manifest.json"
    assert written["finalized_at_utc"] is not None
    assert written["audio_count"] == 1
    assert written["extras"]["probe_text"] == "hello"
    assert written["python_version"]


def test_manifest_records_a_stable_interpreter(tmp_path: Path) -> None:
    """A release-candidate interpreter must not reach the provenance record.

    Ubuntu 22.04's python3.11 is 3.11.0rc1 and shipped in real run manifests
    until 2026-08-05.
    """
    run = RunStore(tmp_path).new_run()
    assert "rc" not in run.manifest.python_version, (
        f"interpreter is {run.manifest.python_version} — this fails until the "
        "devcontainer is rebuilt on the uv-managed stable 3.11 "
        "(Dev Containers: Rebuild Container). It is the gate proving the fix landed."
    )


def test_list_runs_newest_first_and_filtered(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    (tmp_path / "doctor-20260101T000000Z").mkdir()
    (tmp_path / "doctor-20260201T000000Z").mkdir()
    (tmp_path / "generate-20260301T000000Z").mkdir()

    assert [p.name for p in store.list_runs("doctor")] == [
        "doctor-20260201T000000Z",
        "doctor-20260101T000000Z",
    ]
    assert len(store.list_runs()) == 3
    assert RunStore(tmp_path / "nope").list_runs() == []
