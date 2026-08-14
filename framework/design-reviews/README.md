# Design Reviews

## Purpose

Evaluate whether a design is coherent, sufficiently evidenced, manufacturable, verifiable, and ready for its intended next commitment.

## Inputs

- Review scope, configuration, milestone, and decision sought
- Architecture and interface descriptions
- Approved requirements and decisions
- Current risks, assumptions, and engineering changes
- Calculations, tolerance analyses, prototypes, and test evidence
- Manufacturing, assembly, service, and supplier information
- Open findings from prior reviews

## Outputs

- Review summary and evidence inventory
- Findings with severity, owner, and closure criterion
- Blocking and nonblocking gaps
- Linked actions, risks, or change requests
- Recommendation such as `advance`, `conditional`, `hold`, or `unknown`

## Sequence

1. Define the configuration, boundary, review questions, and criteria.
2. Freeze or identify the reviewed evidence set.
3. Check architecture, load and energy paths, interfaces, constraints, and failure modes.
4. Review requirement coverage, calculations, tolerances, prototypes, and tests.
5. Review manufacturing, assembly, inspection, service, and lifecycle considerations.
6. Reconcile previous findings and material changes.
7. Classify new findings and assign owners and closure evidence.
8. Evaluate each readiness criterion independently.
9. Obtain the authorized review disposition.
10. Track findings to verified closure; repeat affected sections after material change.

## State and status model

Reviews move through `planned`, `evidence_ready`, `in_review`, `dispositioned`, and `closed`. Findings use `open`, `accepted`, `mitigating`, `ready_for_verification`, `closed`, or `deferred`. Severity may be configured, but should distinguish blocking issues, significant concerns, minor issues, and observations.

## Provenance and traceability

Record the reviewed configuration or revision, participants and roles, criteria, evidence references, findings, disposition, approver, and time. A later review does not erase earlier findings. Changed evidence is identified explicitly.

## Review and approval gates

- Evidence readiness is checked before the meeting or asynchronous review.
- Every non-unknown criterion cites evidence.
- Blocking findings prevent advancement unless the authorized governance process accepts the risk.
- A conditional disposition lists exact conditions and owners.
- Finding closure requires evidence and reviewer confirmation, not an owner's assertion alone.

## Adaptation

Select review modules appropriate to the product: mechanical, electrical, software, optical, thermal, reliability, safety, manufacturing, or service. Configure criteria to the organization and applicable standards; do not copy unlicensed criteria or use generic thresholds without engineering justification.

## Failure and uncertainty handling

Absent evidence is `unknown`. Conflicting revisions pause the affected assessment. If the review scope or decision authority is ambiguous, issue a preparation gap list rather than a readiness verdict. Material post-review changes reopen affected findings and criteria.
