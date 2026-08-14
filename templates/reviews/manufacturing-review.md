---
type: manufacturing_review
id: "MFG-{{project_id}}-{{sequence}}"
project_id: "{{project_id}}"
status: planned
owner: "{{owner}}"
created: "{{date}}"
updated: "{{date}}"
source_links: ["{{source}}"]
related_ids: []
---

# {{review_title}}

## Manufacturing intent

- Part or assembly:
- Intended process and volume assumption:
- Material assumption:
- Drawing/model revision:
- Supplier input status:

Do not apply generic numerical rules without confirming the process, material, supplier capability, and applicable standards.

## Review checklist

| Area | Question | Evidence | Finding |
|---|---|---|---|
| Process selection | Is the proposed process suitable for geometry, volume, quality, and cost? |  |  |
| Geometry | Are draft, wall transitions, radii, bends, and feature depths compatible with the process? |  |  |
| Access and tooling | Can tools, fixtures, inspection equipment, and operators reach required features? |  |  |
| Datum and inspection | Are functional datums stable, buildable, and measurable? |  |  |
| Assembly | Is sequence clear, mistake-resistant, and serviceable where required? |  |  |
| Capability | Are critical tolerances supported by evidence rather than assumption? |  |  |

## Findings and supplier questions

| ID | Severity | Finding or question | Recommendation | Owner | Disposition |
|---|---|---|---|---|---|
| {{finding_id}} | `blocking | warning | note` | {{finding}} | {{recommendation}} | {{owner}} | `open` |

## Release recommendation

- Recommendation: `release | conditional | hold`
- Residual risks:
- Required approvals:
