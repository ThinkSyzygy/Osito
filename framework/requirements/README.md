# Requirements

## Purpose

Turn stakeholder needs and constraints into uniquely identified, testable, traceable requirements whose approval and verification status are explicit.

## Inputs

- Stakeholder need, source, and rationale
- Applicable configuration, operating context, and interfaces
- Acceptance criteria and verification method
- Priority, owner, dependencies, and constraints
- Regulatory or contractual references that the team is permitted to use

## Outputs

- Requirement records with stable IDs
- Approved requirement baseline
- Trace links to decisions, risks, design elements, changes, and validation evidence
- Verification status and unresolved coverage gaps

## Sequence

1. Capture the need and its source without prematurely prescribing a solution.
2. Rewrite it as one atomic, measurable statement while retaining the original rationale.
3. Identify configuration, boundaries, assumptions, and defined terms.
4. Check for duplicates, contradictions, unverifiable language, and hidden design choices.
5. Define acceptance criteria and a feasible verification method.
6. Review dependencies and downstream impacts.
7. Approve the requirement into a baseline.
8. Link implementation decisions and validation items.
9. Attach evidence and record the verification verdict.
10. Route later changes through engineering change control; never overwrite the approved history.

## State and status model

Suggested states are `draft`, `in_review`, `approved`, `implemented`, `verified`, `failed`, `deferred`, `rejected`, and `retired`. Verification state is separate from approval state: an approved requirement is not automatically implemented or verified.

## Provenance and traceability

Record the originating source, author, approval, baseline revision, and all evidence links. A changed requirement either creates a new revision or supersedes the prior record with bidirectional links. Derived requirements identify their parent need.

## Review and approval gates

- Baseline approval requires a clear statement, rationale, applicability, owner, acceptance criteria, and verification method.
- `verified` requires cited evidence and a reviewer verdict against the approved criteria.
- Scope, threshold, interface, or acceptance changes require impact analysis and approval through the change workflow.
- Waivers and deviations require explicit authority, duration, rationale, and affected configuration.

## Adaptation

Use prose records, tables, or a requirements tool, but retain stable identity and traceability. Teams may configure priority and verification taxonomies. Avoid embedding third-party standard text; cite the authorized source and write only the project-specific requirement needed.

## Failure and uncertainty handling

Ambiguous requirements remain in review with specific questions. Contradictions are recorded as conflicts and not silently reconciled. If a verification method cannot credibly test the statement, revise the requirement before approval. Missing evidence leaves the status unverified.
