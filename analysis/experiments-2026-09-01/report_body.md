warning: `VIRTUAL_ENV=C:\Users\njger\AppData\Local\Programs\Python\Python311` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
## Experiment A — 20 new items on ElevenLabs pinned narration voice

| item | topic | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ (t1−t3) | monotonic? | classification |
|---|---|---:|---:|---:|---:|---:|---|---|
| EMOT01 | EMOT | 19.0s | -19.20 | -21.67 | -20.22 | +1.02 | False | no fade |
| EMOT02 | EMOT | 22.6s | -19.67 | -20.19 | -22.62 | +2.96 | True | FADE |
| EMOT03 | EMOT | 16.9s | -20.15 | -19.82 | -21.20 | +1.04 | False | no fade |
| EMOT04 | EMOT | 18.4s | -22.27 | -23.24 | -23.60 | +1.33 | True | mono-decr (small) |
| EMOT05 | EMOT | 15.4s | -19.30 | -19.59 | -20.50 | +1.20 | True | mono-decr (small) |
| FACT01 | FACT | 24.5s | -20.60 | -21.15 | -22.33 | +1.74 | True | mono-decr (small) |
| FACT02 | FACT | 24.2s | -20.66 | -20.71 | -20.80 | +0.14 | True | mono-decr (small) |
| FACT03 | FACT | 22.0s | -21.25 | -21.52 | -23.45 | +2.21 | True | FADE |
| FACT04 | FACT | 19.2s | -19.72 | -20.10 | -20.68 | +0.96 | True | mono-decr (small) |
| FACT05 | FACT | 23.6s | -23.33 | -22.66 | -23.65 | +0.32 | False | no fade |
| TECH01 | TECH | 18.2s | -20.69 | -21.02 | -21.26 | +0.57 | True | mono-decr (small) |
| TECH02 | TECH | 19.0s | -19.30 | -21.10 | -20.57 | +1.26 | False | no fade |
| TECH03 | TECH | 22.1s | -19.83 | -21.35 | -20.54 | +0.72 | False | no fade |
| TECH04 | TECH | 16.6s | -19.56 | -20.88 | -19.98 | +0.42 | False | no fade |
| TECH05 | TECH | 15.7s | -21.03 | -21.72 | -21.59 | +0.55 | False | no fade |
| WARM01 | WARM | 22.0s | -22.19 | -22.98 | -23.09 | +0.91 | True | mono-decr (small) |
| WARM02 | WARM | 24.2s | -20.95 | -20.35 | -20.12 | -0.83 | False | no fade |
| WARM03 | WARM | 19.4s | -20.66 | -21.90 | -21.54 | +0.88 | False | no fade |
| WARM04 | WARM | 17.8s | -20.14 | -20.58 | -19.82 | -0.31 | False | no fade |
| WARM05 | WARM | 17.6s | -21.85 | -22.24 | -21.77 | -0.08 | False | no fade |

**A totals**: 2 / 20 items fade (Δ ≥ 2 dB AND monotonically decreasing across thirds). 9 / 20 monotonic decreasing (any magnitude).

**Per topic (fade / total)**:
- TECH: 0 / 5
- WARM: 0 / 5
- FACT: 1 / 5
- EMOT: 1 / 5

## Experiment B — L03 on 5 different ElevenLabs voices

| voice | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ (t1−t3) | monotonic? | classification |
|---|---:|---:|---:|---:|---:|---|---|
| antoni | 84.5s | -18.16 | -17.80 | -17.93 | -0.22 | False | no fade |
| bella | 79.6s | -17.23 | -18.14 | -17.66 | +0.43 | False | no fade |
| charlotte_pinned | 83.1s | -20.43 | -20.94 | -23.22 | +2.79 | True | FADE |
| josh | 87.2s | -22.60 | -24.70 | -25.52 | +2.92 | True | FADE |
| rachel | 82.5s | -25.67 | -26.01 | -26.32 | +0.65 | True | mono-decr (small) |

**B totals**: 2 / 5 voices fade on L03.

## Experiment C — L03 split into halves

| segment | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ (t1−t3) | monotonic? | classification |
|---|---:|---:|---:|---:|---:|---|---|
| l03_half1 | 40.0s | -20.19 | -21.20 | -22.09 | +1.89 | True | mono-decr (small) |
| l03_half2 | 40.7s | -20.91 | -22.12 | -21.72 | +0.81 | False | no fade |

## Experiment E — alt-voice sweep (drift stats for reference; full T6-style needs quality/wer analyzers)

| vendor | item | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ | mono? |
|---|---|---:|---:|---:|---:|---:|---|
| deepgram | L01 | 76.9s | -26.94 | -26.60 | -26.23 | -0.71 | False |
| deepgram | L02 | 79.6s | -26.34 | -26.71 | -26.47 | +0.13 | False |
| deepgram | L03 | 78.7s | -26.66 | -27.01 | -26.37 | -0.29 | False |
| deepgram | L04 | 95.8s | -25.10 | -25.98 | -25.82 | +0.71 | False |
| deepgram | L05 | 93.0s | -26.91 | -27.70 | -25.58 | -1.34 | False |
| deepgram | L06 | 82.6s | -26.61 | -27.22 | -28.21 | +1.60 | True |
| deepgram | L07 | 104.6s | -26.01 | -26.06 | -26.18 | +0.17 | True |
| deepgram | L08 | 76.4s | -24.43 | -25.40 | -25.59 | +1.16 | True |
| fish | L01 | 74.0s | -17.18 | -18.41 | -17.63 | +0.45 | False |
| fish | L02 | 74.9s | -17.78 | -17.58 | -18.38 | +0.60 | False |
| fish | L03 | 77.2s | -18.05 | -18.42 | -18.56 | +0.52 | True |
| fish | L04 | 85.3s | -17.23 | -17.81 | -17.66 | +0.43 | False |
| fish | L05 | 86.1s | -17.58 | -17.86 | -19.09 | +1.51 | True |
| fish | L06 | 79.4s | -17.25 | -18.44 | -18.12 | +0.86 | False |
| fish | L07 | 104.8s | -18.02 | -17.44 | -18.06 | +0.05 | False |
| fish | L08 | 68.2s | -17.28 | -17.96 | -18.40 | +1.12 | True |
| google | L01 | 77.0s | -22.11 | -22.48 | -23.13 | +1.02 | True |
| google | L02 | 81.8s | -21.57 | -21.34 | -22.29 | +0.72 | False |
| google | L03 | 78.9s | -20.49 | -22.88 | -22.76 | +2.27 | False |
| google | L04 | 98.7s | -22.53 | -20.99 | -21.80 | -0.72 | False |
| google | L05 | 90.8s | -20.90 | -21.59 | -21.35 | +0.45 | False |
| google | L06 | 82.0s | -21.96 | -21.39 | -22.70 | +0.74 | False |
| google | L07 | 106.8s | -22.64 | -22.23 | -22.84 | +0.20 | False |
| google | L08 | 76.5s | -21.53 | -22.08 | -20.62 | -0.91 | False |
| openai | L01 | 80.5s | -24.99 | -25.56 | -26.28 | +1.29 | True |
| openai | L02 | 78.8s | -24.81 | -26.08 | -27.70 | +2.89 | True |
| openai | L03 | 86.3s | -24.37 | -27.68 | -26.71 | +2.35 | False |
| openai | L04 | 94.8s | -23.27 | -26.85 | -27.02 | +3.75 | True |
| openai | L05 | 91.1s | -23.91 | -25.42 | -25.26 | +1.35 | False |
| openai | L06 | 86.5s | -24.73 | -25.58 | -26.15 | +1.42 | True |
| openai | L07 | 98.9s | -26.80 | -26.12 | -26.82 | +0.02 | False |
| openai | L08 | 77.9s | -27.00 | -26.35 | -27.11 | +0.12 | False |
