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
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-dev \
        python3.11-venv \
        python3-pip \
        ffmpeg \
        libsndfile1 \
        sox \
        build-essential \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# --- uv (fast Python package manager) ---
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /workspace

# Copy just the project metadata first for layer caching
COPY pyproject.toml README.md* CLAUDE.md* ./
COPY src ./src

# Base + admin + dev deps (analyzer extras added below with heavier install)
RUN uv sync --extra admin --extra dev

# Analyzer extras — installed separately because they include large CUDA wheels
# and take 10+ minutes on first build. Cached in a separate layer.
RUN uv sync --extra analyze --extra admin --extra dev

# VERSA / TTSDS2 / NeMo installs — done as a separate RUN so partial failures
# don't invalidate the extras layer above.
# Parakeet TDT ships via NeMo toolkit. TTSDS2 and Audiobox Aesthetics are pip-installable.
RUN uv pip install --system \
        "nemo-toolkit[asr]>=2.0" \
        "ttsds>=2.0" \
        "audiobox-aesthetics>=0.0.3" \
    || echo "WARN: analyzer extras deferred to first analyze run"

# Sanity check that CUDA is visible at build time (does not fail build if not)
RUN python -c "import torch; print(f'torch={torch.__version__} cuda={torch.cuda.is_available()}')" \
    || echo "WARN: torch/CUDA check deferred to runtime"

CMD ["/bin/bash"]
