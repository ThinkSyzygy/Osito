---
type: tolerance_analysis
id: "TOL-{{project_id}}-{{sequence}}"
project_id: "{{project_id}}"
status: draft
owner: "{{owner}}"
created: "{{date}}"
updated: "{{date}}"
source_links: ["{{source}}"]
related_ids: []
---

# {{tolerance_title}}

## Definition

- Functional response:
- Failure mode:
- Applicable configuration:
- Datum and stack path:
- Sign convention:
- Units:
- Functional lower limit:
- Functional upper limit:

Stop if geometry meaning, units, signs, tolerances, or limits are ambiguous.

## Contributors

For each term, define the signed coefficient and the lower/upper deviation of its response contribution from nominal.

| ID | Description | Coefficient | Nominal | Lower tol | Upper tol | Units | Source or assumption | Basis |
|---|---|---:|---:|---:|---:|---|---|---|
| {{term_id}} | {{description}} | {{coefficient}} | {{nominal}} | {{lower_tolerance}} | {{upper_tolerance}} | {{units}} | {{source}} | `measured | specified | calculated | assumed` |

## Equations

For response `R = B + Σ(cᵢxᵢ)`:

- Compute nominal response from nominal inputs.
- Convert each tolerance into signed response deviations `dᵢ⁻ ≤ 0 ≤ dᵢ⁺`.
- Worst-case bounds: `R_min = R_nom + Σdᵢ⁻` and `R_max = R_nom + Σdᵢ⁺`.
- If independent, centered variation is a defensible screening assumption, RSS bounds are `R_nom - √Σ(dᵢ⁻)²` and `R_nom + √Σ(dᵢ⁺)²`.

RSS is not a yield prediction unless distribution and tolerance-to-standard-deviation assumptions are explicitly defined and validated.

## Results and margins

| Method | Minimum response | Maximum response | Lower-limit margin | Upper-limit margin | Verdict |
|---|---:|---:|---:|---:|---|
| Worst case |  |  |  |  |  |
| RSS screen |  |  |  |  |  |

## Dominant contributors and sensitivity

- Largest worst-case terms:
- Largest squared RSS terms:
- Assumed or low-confidence inputs:
- One-at-a-time sensitivity:

## Verification and escalation

- Independent recomputation:
- Physical or dimensional verification:
- Escalate for nonlinear geometry, correlation, process bias, mixed units, uncertain capability, or material safety/reliability consequences.

## Review

- Reviewer:
- Disposition: `approved | revise | blocked`
- Review date:
