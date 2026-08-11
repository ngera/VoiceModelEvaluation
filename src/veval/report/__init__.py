"""Phase G report layer.

Consumes `analysis/score.json` and emits `site/`:
    charts.py  - Plotly (interactive HTML) + Altair (static PNG)
    tables.py  - markdown tables (survivors, robustness, correlations)
    memos.py   - memo templates with data slots

The chart division:
    Plotly    -> admin page 5 (Frontier) - interactive dashboards
    Altair    -> site/*.png              - frozen-in-time for the case study
"""

from __future__ import annotations
