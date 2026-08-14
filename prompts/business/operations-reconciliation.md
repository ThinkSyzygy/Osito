# Business Operations Reconciliation

Use this prompt for time-export normalization, invoice preparation, supplier-action summaries, or another bounded business record review.

## Prompt

```text
Operation: <time reconciliation | billing draft | supplier follow-up | other>
Source artifact: <immutable source reference>
Period and scope: <scope>
Approved mappings, rates, terms, or rounding policy: <policy references>
Requested output: <draft or review artifact>
External destination, if any: <destination or none>

Preserve the raw source. Work only within the stated period and scope.

1. Validate required fields, dates, identities or project mappings, and nonnegative quantities.
2. Separate confirmed data, assumptions, exceptions, and unresolved mappings.
3. Apply only the supplied approved policy.
4. Preserve source descriptions unless a documented normalization is required.
5. Calculate line results, subtotals, and totals deterministically.
6. Recompute totals independently and reconcile them to the source.
7. For communications, separate confirmed outcomes, open questions, and action items; do not invent recipients, owners, dates, commitments, or decisions.

Return:
## Scope and source
## Policy applied
## Validated facts
## Assumptions and exceptions
## Reconciled output or draft
## Independent total or consistency check
## Unresolved items
## Proposed external action
## Explicit approval required

Do not guess rates, terms, mappings, identities, or recipients. Do not send, upload, purchase, pay, publish, or mark the operation complete without explicit approval for that exact destination and action. If reconciliation fails, stop before producing a final artifact.
```
