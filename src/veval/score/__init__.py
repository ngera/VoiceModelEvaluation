"""Phase G — scoring layer.

Pure functions from `analysis/<run_id>/*.json` + `configs/gates.yaml` +
`analysis/bt_fit.json` -> `analysis/score.json`. Modules:

    gates.py         - apply per-use-case gates -> survivor list
    frontier.py      - Pareto frontier + CI-domination rule
    robustness.py    - robustness_points sweep from gates.yaml
    hi_loader.py     - Humanness Index snapshot loader
    correlations.py  - Spearman rho across D3, D4, HI
"""

from __future__ import annotations
