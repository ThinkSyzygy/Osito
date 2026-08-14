# Action Management

## Purpose

Track concrete work with clear ownership, dependencies, completion evidence, and links to the engineering reason the action exists.

## Inputs

- Action statement and intended outcome
- Source, related record, or initiating decision
- Owner, priority, dependencies, blocker, and target date if known
- Completion criterion and expected evidence

## Outputs

- Current action register or action records
- Priority and dependency views
- Escalations for blocked or overdue work
- Verified completion and closure history

## Sequence

1. Capture the action as a specific observable outcome.
2. Search for an existing action before creating a duplicate.
3. Link the source decision, risk, requirement, review finding, or meeting.
4. Confirm owner, dependency, completion criterion, and target timing.
5. Prioritize against project goals and active blockers.
6. Update status as work progresses; record blockers separately from inactivity.
7. Attach deliverable or verification evidence.
8. Obtain closure confirmation when the result affects another controlled record.
9. Close or cancel with rationale while retaining history.

## State and status model

Suggested states are `proposed`, `open`, `in_progress`, `blocked`, `ready_for_review`, `done`, `canceled`, and `superseded`. `Done` means the completion criterion is met; `canceled` means the work is intentionally no longer required.

## Provenance and traceability

Each action records its origin, related IDs, owner changes, material status transitions, deliverables, and closure evidence. A replacement action links to the one it supersedes.

## Review and approval gates

- Assignment is confirmed by the accountable owner or project lead.
- Safety, release, gate, or customer-facing actions require reviewer confirmation before `done`.
- Canceling an action tied to an open risk, requirement, or finding requires disposition of that parent record.
- Bulk AI-generated actions remain proposals until reviewed.

## Adaptation

Teams may keep actions in Markdown, an issue tracker, or a task service. Avoid duplicating authority across systems: designate one canonical action source and use other views as synchronized projections.

## Failure and uncertainty handling

Unknown ownership leaves the action proposed and visible. Missing dates are not invented. Ambiguous completion is `ready_for_review`, not done. Conflicting copies are reconciled through stable IDs and change history rather than whichever copy appears newest.
