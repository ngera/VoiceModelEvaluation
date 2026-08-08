"""Phase F — human judgment layer.

The only phase with a rating loop. Everything here stays local (no
hosted rating page in v1; §10 future work). Modules:

    loudness.py    - -18 LUFS normalization (mandatory before rating)
    pair_builder.py - deterministic (system, system, use_case) pairs
    manifest.py     - per-rater manifest read/write
    bt.py           - Bradley-Terry fit + clustered bootstrap CIs

Rating UI lives in `rating/index.html` (static, opens from filesystem).
"""

from __future__ import annotations
