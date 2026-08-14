---
type: calculation_review
id: "CALC-{{project_id}}-{{sequence}}"
project_id: "{{project_id}}"
status: draft
owner: "{{owner}}"
created: "{{date}}"
updated: "{{date}}"
source_links: ["{{source}}"]
related_ids: []
---

# {{calculation_title}}

## Question and response

- Engineering question:
- Output quantity:
- Required decision:
- Applicable configuration:

## Inputs

| ID | Quantity | Value | Units | Source | Basis | Confidence |
|---|---|---:|---|---|---|---|
| {{input_id}} | {{quantity}} | {{value}} | {{units}} | {{source}} | `measured | specified | calculated | assumed` | {{confidence}} |

## Assumptions and boundary conditions

- Assumption:
- Boundary condition:
- Applicability limit:

## Method

List equations, sign conventions, coordinate systems, unit conversions, and numerical methods. Cite externally sourced equations or methods.

## Results

| Result | Value | Units | Precision rationale |
|---|---:|---|---|
| {{result}} | {{value}} | {{units}} | {{precision}} |

## Checks

- [ ] Units are dimensionally consistent.
- [ ] Signs and coordinate conventions were checked.
- [ ] Limiting and simple cases behave as expected.
- [ ] An independent recomputation agrees.
- [ ] Sensitivity to uncertain inputs is reported.
- [ ] Results are compared with physical intuition or test evidence.

## Interpretation

Separate the calculated result from the engineering recommendation. State uncertainty and conditions that would change the recommendation.

## Review

- Reviewer:
- Independent method:
- Disposition: `approved | revise | inconclusive`
- Review date:
