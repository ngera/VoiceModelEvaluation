"""Phase G — scoring layer.

Pure functions from `analysis/<run_id>/*.json` + `configs/gates.yaml` +
`analysis/bt_fit.json` -> `analysis/score.json`. Modules:

    gates.py         - apply per-use-case gates -> survivor list
    frontier.py      - Pareto frontier + CI-domination rule
    robustness.py    - robustness_points sweep from gates.yaml
    correlations.py  - Spearman rho across machine-quality signals + D4
"""

from __future__ import annotations
