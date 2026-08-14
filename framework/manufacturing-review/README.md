# Manufacturing Review

## Purpose

Assess whether a part or assembly can be produced, inspected, assembled, serviced, and scaled with acceptable risk before an expensive or difficult-to-reverse commitment.

## Inputs

- Reviewed design revision and intended manufacturing process
- Materials, finishes, interfaces, and critical characteristics
- Expected production context and quality objectives
- Assembly sequence, tooling, fixturing, inspection, and service concepts
- Tolerance analyses, test evidence, known risks, and prior findings
- Supplier or manufacturing-partner feedback when available

## Outputs

- Findings with severity, owner, rationale, and closure evidence
- Recommended design or process changes
- Manufacturing risks and validation actions
- Supplier question and response log
- Readiness disposition for the reviewed commitment

## Sequence

1. Confirm the exact design revision, process, scope, and commitment being reviewed.
2. Check whether the process is appropriate for geometry, material, finish, quality, and scale.
3. Review feature accessibility, forming or removal constraints, joining, finishing, and inspection.
4. Review tolerance capability and measurement strategy for critical characteristics.
5. Walk the assembly sequence, operator and tool access, error-proofing, handling, fixturing, and serviceability.
6. Identify likely variation, defect, rework, maintenance, and supply risks.
7. Collect supplier recommendations and evaluate performance, risk, cost, schedule, and downstream effects.
8. Classify findings and decide whether each is accepted, rejected with rationale, or requires investigation.
9. Complete required prototypes, process trials, measurements, or tests.
10. Obtain the authorized readiness disposition and track findings to closure.

## State and status model

Reviews use `planned`, `in_review`, `conditional`, `ready`, `not_ready`, and `closed`. Findings use `open`, `investigating`, `mitigating`, `accepted`, `ready_for_verification`, `closed`, or `deferred`.

## Provenance and traceability

Record design revision, process assumptions, participants, supplier responses, finding locations, evidence, dispositions, approvals, and affected changes. Supplier advice remains attributable input, not automatic project authority.

## Review and approval gates

- The reviewed design and process must be unambiguous.
- Blocking findings prevent release or commitment until resolved or formally accepted by authorized risk owners.
- Supplier-driven design changes use the engineering change workflow.
- Closure requires evidence that the finding criterion is met.
- Tooling, purchase, production release, or external handoff remains an explicit human authorization.

## Adaptation

Create process-specific modules using independently verified engineering guidance and supplier capability data. Avoid copying proprietary supplier rules or licensed standards. Review depth should scale with irreversibility, consequence, novelty, and uncertainty.

## Failure and uncertainty handling

Unknown supplier capability or missing process data becomes a risk and validation action. Conflicting supplier recommendations remain visible until resolved. If the design revision changes materially, reopen affected findings rather than carrying forward an unsupported disposition.
