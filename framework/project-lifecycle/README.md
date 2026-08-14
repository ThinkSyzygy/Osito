# Project Lifecycle

## Purpose

Provide a configurable path from project initiation through execution, transfer, completion, and archive without confusing schedule progress with evidence of technical readiness.

## Inputs

- Project charter, intended outcome, and scope boundaries
- Stakeholders, accountable roles, and approval authority
- Constraints, assumptions, requirements, and initial risks
- Chosen lifecycle phases and gate criteria
- Confidentiality, retention, and external-sharing rules

## Outputs

- Approved project overview and lifecycle state
- Phase or milestone plan
- Gate reviews and evidence gaps
- Closure report and archive manifest
- Links to requirements, decisions, risks, actions, changes, tests, and lessons

## Sequence

1. **Initiate:** record purpose, scope, boundary, roles, constraints, and success criteria.
2. **Discover:** capture requirements, assumptions, major risks, architecture options, and research needs.
3. **Plan:** choose lifecycle phases, gate criteria, prototypes, validation methods, and ownership.
4. **Execute:** maintain current records while preserving source evidence.
5. **Review:** assess each gate criterion independently against linked evidence.
6. **Transition:** advance only after authorized disposition of blockers and carried risks.
7. **Transfer or release:** confirm documentation, manufacturing or operational readiness, and ownership handoff.
8. **Close:** disposition open work, record outcomes, and identify reusable lessons.
9. **Archive:** freeze the final authority map, preserve evidence, create a manifest, verify links, and test restoration.

## State and status model

Suggested project states are `proposed`, `active`, `on_hold`, `closing`, `completed`, `canceled`, and `archived`. Phase readiness is tracked separately as `not_reviewed`, `in_review`, `ready`, `conditional`, `not_ready`, or `unknown`.

A project can be active while a gate is not ready. A date passing does not change readiness.

## Provenance and traceability

Each lifecycle transition references its review, evidence set, accepted risks, approver, and timestamp. Current phase summaries link to detailed records instead of duplicating their history. Historical reviews remain available after later transitions.

## Review and approval gates

- Project activation requires an approved charter and boundary.
- Each phase transition requires criterion-level evidence or an explicit, authorized risk disposition.
- Cancellation and closure require disposition of open actions, assets, obligations, and evidence.
- Archive status is applied only after manifest, link, access, and restoration checks.

## Adaptation

Teams may use named hardware phases, software milestones, regulatory stages, or a simple discovery/build/verify sequence. Keep criteria configurable and evidence-based. Optional phases should be omitted explicitly, not silently skipped.

## Failure and uncertainty handling

Missing evidence produces `unknown`, not a pass. Conflicting evidence blocks the affected criterion. If gate criteria are unclear, produce a gap analysis rather than a readiness claim. If ownership or archive retention is unresolved, keep the project in `closing`.
