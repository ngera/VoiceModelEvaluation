# CUDA 12.4 + cuDNN devel base gives Parakeet (NeMo) and faster-whisper GPU support.
# devel (not runtime) because some pip installs compile CUDA kernels (e.g. flash-attn).
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

# --- System deps ---
# ffmpeg: audio decode/encode for hygiene + loudness normalization
# libsndfile1: soundfile / pyloudnorm
# sox: fallback resampling
# build-essential: some pip packages compile C extensions
# git: pip installs from git repos (VERSA, TTSDS2 sometimes)
#
# NOTE: python3.11 is deliberately NOT installed from apt. Ubuntu 22.04 ships
# `python3.11` as 3.11.0rc1 (a 2022 release candidate), which we ran until
# 2026-08-05 — see documentation/IMPLEMENTATION_PLAN.md. uv installs a stable
# 3.11.x below instead. cp311 wheels are ABI-compatible across patch releases,
# so the analyzer stack is unaffected by the switch.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        sox \
        build-essential \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- uv (fast Python package manager) ---
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

# --- Python: uv-managed stable 3.11, not Ubuntu's rc1 ---
ENV UV_PYTHON=3.11
RUN uv python install 3.11 \
    && uv run --no-project python -VV

WORKDIR /workspace

# Copy just the project metadata first for layer caching.
# uv.lock is committed, so builds resolve to the pinned instrument, not "latest".
COPY pyproject.toml uv.lock README.md* CLAUDE.md* ./
COPY src ./src

# One venv, addressed absolutely. The repo mounts at /workspaces/<name> while
# this image builds at /workspace, so without UV_PROJECT_ENVIRONMENT uv creates
# a second venv depending on CWD. Putting it on PATH also means bare `python`
# is the project interpreter rather than whatever apt left behind.
ENV VIRTUAL_ENV=/workspace/.venv \
    UV_PROJECT_ENVIRONMENT=/workspace/.venv \
    PATH="/workspace/.venv/bin:${PATH}"

# Base + admin + dev deps (analyzer extras added below with heavier install)
RUN uv sync --extra admin --extra dev

# Analyzer extras — installed separately because they include large CUDA wheels
# and take 10+ minutes on first build. Cached in a separate layer.
RUN uv sync --extra analyze --extra admin --extra dev

# VERSA / TTSDS2 / NeMo installs — done as a separate RUN so partial failures
# don't invalidate the extras layer above.
# Parakeet TDT ships via NeMo toolkit. TTSDS2 and Audiobox Aesthetics are pip-installable.
# NOT --system: that installed them into the system interpreter while the app
# runs from the venv, so `import nemo` would have failed at Phase E despite a
# green build.
RUN uv pip install \
        "nemo-toolkit[asr]>=2.0" \
        "ttsds>=2.0" \
        "audiobox-aesthetics>=0.0.3" \
    || echo "WARN: analyzer extras deferred to first analyze run"

# Sanity check the interpreter is a stable release and CUDA is visible.
# Neither fails the build; GPU is absent during image build on most hosts.
# Hard-fail: a release-candidate interpreter must never reach a run manifest again.
RUN python -VV \
    && python -c "import sys; assert sys.version_info[:2] == (3, 11) and 'rc' not in sys.version, f'non-stable interpreter: {sys.version}'"

# Soft-fail: GPU is usually absent during image build, so this is informational.
RUN python -c "import torch; print(f'torch={torch.__version__} cuda={torch.cuda.is_available()}')" \
    || echo "WARN: torch/CUDA check deferred to runtime"

CMD ["/bin/bash"]
