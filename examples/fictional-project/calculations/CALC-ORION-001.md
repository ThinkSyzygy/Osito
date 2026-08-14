---
type: tolerance_analysis
id: CALC-ORION-001
project_id: ORION
status: approved
owner: Morgan Vale
created: 2031-04-18
updated: 2031-04-22
fictional: true
source_links: ["../decisions/DEC-ORION-001.md"]
related_ids: [DR-ORION-001]
---

# Rear-cover minimum side clearance screen

> **Fictional example:** every dimension, tolerance, assumption, and result is invented.

## Question

Does the proposed rear-cover concept retain at least 0.10 mm clearance on the tighter side under the stated one-dimensional prototype allowances?

This is an educational one-dimensional tolerance screen. It is not a drawing release, process-capability study, or yield prediction.

## Definition

Response:

`minimum one-side clearance = 0.5 × opening width - 0.5 × cover width - absolute centering offset`

- Units: mm
- Opening nominal: 70.00
- Cover nominal: 69.10
- Centering-offset nominal: 0.00
- Nominal response: 0.45
- Functional lower limit: 0.10

## Contributors

| ID | Contribution | Coefficient magnitude | Two-sided allowance | Response allowance | Basis |
|---|---|---:|---:|---:|---|
| T1 | Opening width | 0.5 | ±0.25 mm | ±0.125 mm | Fictional design allowance |
| T2 | Cover width | 0.5 | ±0.20 mm | ±0.100 mm | Fictional design allowance |
| T3 | Centering offset | 1.0 | ±0.10 mm | ±0.100 mm | Fictional assembly assumption |

The signs were checked so that a smaller opening, larger cover, or adverse offset reduces clearance.

## Results

- Worst-case variation: `0.125 + 0.100 + 0.100 = 0.325 mm`
- Worst-case range: `0.45 ± 0.325 = 0.125 to 0.775 mm`
- Worst-case lower-limit margin: `0.125 - 0.10 = 0.025 mm`
- RSS variation: `√(0.125² + 0.100² + 0.100²) = 0.189 mm` after rounding
- RSS screening range: `0.261 to 0.639 mm` after rounding
- RSS lower-limit margin: `0.161 mm` after rounding

## Interpretation

The fictional stack passes the lower limit under the stated worst-case allowances, but only by 0.025 mm. The centering-offset term is assumed rather than measured, and the screen does not account for nonlinear contact or part deformation. The design review therefore treats the interface as needing first-build inspection.

## Independent review

Priya North independently recomputed the nominal, worst-case, and RSS values on 2031-04-22 and agreed within the shown rounding. Morgan Vale approved the analysis for this fictional prototype only.
