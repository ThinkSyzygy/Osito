---
type: invoice_data_preparation
id: "INV-{{project_id}}-{{period}}"
project_id: "{{project_id}}"
status: drafted
owner: "{{owner}}"
created: "{{date}}"
updated: "{{date}}"
source_links: ["{{source}}"]
related_ids: []
---

# {{period}} invoice-data preparation

## Controls

- Preserve the raw export unchanged.
- Load rates from an access-controlled configuration supplied at runtime.
- Document time-zone, grouping, rounding, currency, and tax assumptions.
- Stop when a rate or required description is missing.

## Transformation

| Source row ID | Work date | Description | Raw hours | Rounded hours | Rate key | Amount |
|---|---|---|---:|---:|---|---:|
| {{row_id}} | {{date}} | {{description}} | {{raw_hours}} | {{rounded_hours}} | {{rate_key}} | {{amount}} |

## Reconciliation

- Raw source total:
- Grouped pre-round total:
- Rounded billable total:
- Amount recomputed independently:
- Difference and explanation:

## Review and release

- Prepared by:
- Reviewed by:
- Client-facing description review:
- Upload/send approved:
- Readback verified:
