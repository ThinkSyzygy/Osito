# Business Operations

## Purpose

Apply the same evidence, reconciliation, approval, and provenance discipline to time records, billing preparation, supplier communication, purchasing support, and other engineering-adjacent operations.

## Inputs

- Authorized raw export, correspondence, or request
- Period, scope, project mapping, and accountable owner
- Verified rates, terms, rounding rules, or approval policy
- Destination and external-action intent
- Privacy, retention, tax, contractual, and access constraints

## Outputs

- Reconciled working table or draft artifact
- Validation and exception summary
- Approval record
- Optional exported, uploaded, or sent artifact after authorization
- Audit link to the unchanged source

## Sequence

1. Preserve the raw input and record its source and scope.
2. Validate required fields, dates, mappings, values, and nonnegative quantities.
3. Resolve duplicates and ambiguous mappings without discarding source rows.
4. Apply the approved grouping, rounding, rate, or formatting policy.
5. Calculate line values, subtotals, and totals deterministically.
6. Recompute totals independently and reconcile to the source.
7. Surface unknown rates, malformed rows, missing recipients, or contractual uncertainty.
8. Produce a draft or review-ready artifact.
9. Obtain explicit approval for the business result and any external action.
10. If requested, send or upload through the authorized system and verify the destination by readback.
11. Retain the audit summary according to policy without exposing private rates or identities.

For external follow-up messages, separate confirmed outcomes, open questions, and action items. Do not invent recipients, owners, dates, commitments, or decisions. Drafting is the default; sending is a separate action.

## State and status model

Suggested states are `received`, `validating`, `needs_review`, `reconciled`, `drafted`, `approved`, `exported`, `sent`, `void`, and `archived`. A local artifact may be reconciled without being approved for external use.

## Provenance and traceability

Record the source hash or immutable reference, transformation policy and version, mappings, exceptions, independent total check, reviewer, destination verification, and timestamps. Keep sensitive rate cards and identity mappings outside public examples.

## Review and approval gates

- Unknown or ambiguous rates, terms, mappings, totals, or recipients block finalization.
- External send, upload, purchase, payment, or publication always requires explicit authorization.
- Changes to raw data are prohibited; corrections are applied as documented transformations.
- Destination verification is required before reporting an external operation complete.

## Adaptation

Provider-specific importers should normalize into a documented internal schema. Keep policy separate from transport so teams can change time trackers, spreadsheets, mail systems, or storage providers without changing approval semantics.

## Failure and uncertainty handling

Never guess a rate, identity, contractual term, or financial total. Preserve exception rows for review. If reconciliation fails, return the mismatch and stop before export. If an external operation cannot be verified, report it as unconfirmed rather than retrying blindly.
