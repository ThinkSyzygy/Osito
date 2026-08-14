# Osito Framework

Osito is an operating framework for keeping engineering work current, traceable, and reviewable while using AI assistants. The framework separates source evidence, approved operational state, and generated views so that convenience never silently becomes authority.

## Purpose

Provide a coherent control layer for engineering knowledge, project state, technical work, review, and AI-assisted proposals without granting software autonomous engineering authority.

## System-wide principles

1. **Bound the work.** Every task names its project, subsystem, time window, and permitted sources.
2. **Preserve evidence.** Meeting notes, test reports, supplier responses, and research sources remain intact. Corrections are identified rather than silently rewritten.
3. **Maintain explicit current state.** Requirements, decisions, risks, actions, changes, and validation records have stable identities and controlled statuses.
4. **Propose, review, then apply.** AI interpretation is a proposal. Deterministic checks can validate structure, but only an authorized reviewer can approve an engineering or business decision.
5. **Keep uncertainty visible.** Missing, conflicting, stale, or ambiguous information is labeled. It is never converted into a confident conclusion.
6. **Treat generated material as a view.** Briefings, dashboards, compiled context, and exports point back to canonical records and can be regenerated.
7. **Validate after change.** Approved mutations are checked for provenance, lifecycle integrity, broken relationships, and unintended scope.

## Inputs

- Authorized project sources and confidentiality boundaries
- Team roles, approval authority, and lifecycle policies
- Record schemas, controlled statuses, and relationship rules
- Engineering evidence, current state, and requested task scope

## Outputs

- Traceable current-state records
- Reviewable proposals and approval artifacts
- Evidence-linked engineering analyses and reviews
- Regenerable briefings, dashboards, validation reports, and exports

## Operating sequence

1. Establish project and source boundaries.
2. Load the smallest authoritative context needed.
3. Separate facts, assumptions, inferences, and unknowns.
4. Produce a structured proposal or analysis.
5. Validate identity, provenance, lifecycle, and internal consistency.
6. Obtain explicit approval for controlled state or external action.
7. Apply the approved change with freshness and idempotency safeguards.
8. Validate again and regenerate derived views.

## Common record envelope

Projects may use Markdown, YAML, JSON, a database, or another durable format. Whatever the storage technology, current-state records should carry the equivalent of:

```yaml
id: stable-unique-id
type: requirement | decision | risk | action | change | test | other
project: project-key
title: concise-title
status: controlled-status
owner: accountable-role-or-person
created_at: timestamp
updated_at: timestamp
source_refs: []
related_ids: []
supersedes: []
review:
  state: pending | approved | rejected
  reviewer: null
  reviewed_at: null
```

Record bodies should state the current condition, supporting evidence, unresolved questions, and the next review or completion criterion.

## State and status model

Each record type owns a controlled lifecycle. Status changes are explicit events with an actor, time, reason, and evidence. Closed, rejected, retired, and superseded records remain historical; generated outputs use freshness states rather than engineering approval states.

## Provenance and traceability

Material claims link to source evidence or approved records. Generated artifacts disclose their input set and freshness. Changes preserve stable IDs and create reciprocal relationships for dependencies and supersession.

## Workflow map

| Area | Primary concern |
|---|---|
| [Knowledge architecture](knowledge-architecture/README.md) | Authority, record types, relationships, and generated views |
| [Project lifecycle](project-lifecycle/README.md) | Project initiation, gates, closure, and archive |
| [Requirements](requirements/README.md) | Testable needs, baselines, verification, and change |
| [Decision records](decision-records/README.md) | Options, rationale, approval, and supersession |
| [Design reviews](design-reviews/README.md) | Evidence-based maturity assessment and findings |
| [Engineering changes](engineering-changes/README.md) | Controlled changes to approved baselines |
| [Risk management](risk-management/README.md) | Uncertainty, exposure, mitigation, and acceptance |
| [Meeting ingestion](meeting-ingestion/README.md) | Evidence preservation and proposed state changes |
| [Action management](action-management/README.md) | Ownership, dependencies, completion evidence |
| [Research](research/README.md) | Traceable inquiry and evidence synthesis |
| [Lessons learned](lessons-learned/README.md) | Safe generalization of experience |
| [Tolerance analysis](tolerance-analysis/README.md) | Dimensional variation and functional margin |
| [Calculation review](calculation-review/README.md) | Auditable engineering calculations |
| [Manufacturing review](manufacturing-review/README.md) | Process feasibility, assembly, and supplier feedback |
| [Business operations](business-operations/README.md) | Reconciliation, communication, and external-action controls |

## Workflow entry points

Use the workflow guides for policy and sequence, the [template library](../templates/README.md) for durable records, and the [prompt library](../prompts/README.md) for bounded AI-assisted drafting. Common combinations include:

| Goal | Workflow | Record or prompt |
|---|---|---|
| Capture and verify a need | [Requirements](requirements/README.md) | [Requirement template](../templates/requirements/requirement.md) |
| Preserve a meeting and propose updates | [Meeting ingestion](meeting-ingestion/README.md) | [Meeting prompt](../prompts/meetings/meeting-change-proposal.md) and [change-set template](../templates/meetings/proposed-change-set.md) |
| Record an approved choice | [Decision records](decision-records/README.md) | [Decision template](../templates/decisions/decision-record.md) |
| Evaluate maturity | [Design reviews](design-reviews/README.md) | [Review prompt](../prompts/reviews/evidence-based-review.md) and [design-review template](../templates/reviews/design-review.md) |
| Review dimensional variation | [Tolerance analysis](tolerance-analysis/README.md) | [Tolerance template](../templates/engineering/tolerance-analysis.md) |
| Control a baseline change | [Engineering changes](engineering-changes/README.md) | [Engineering-change template](../templates/engineering/engineering-change.md) |

## Review and approval gates

Reading, organizing, calculating, and drafting are not approval. An AI assistant must not independently:

- approve a requirement, decision, risk acceptance, design gate, or engineering change;
- mark a test as passed without cited evidence and defined criteria;
- close work merely because discussion stopped;
- send external messages, place orders, upload business records, or publish artifacts;
- choose between conflicting technical values; or
- broaden one project's context into another project.

Each workflow below identifies its own approval gates and safe failure behavior.

## Adaptation

Start with the smallest record set that supports the team's work. Add fields only when they drive a decision, search, validation, or audit need. Controlled statuses, required evidence, and approval roles should be configured centrally and tested with fictional fixtures before live adoption.

## Failure and uncertainty handling

Missing or conflicting evidence is reported explicitly. Unknown authority, stale context, invalid lifecycle transitions, and cross-boundary data stop affected work. Osito favors a precise gap list and reversible proposal over a confident but unsupported result.
