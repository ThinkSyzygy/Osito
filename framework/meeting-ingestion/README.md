# Meeting Ingestion

## Purpose

Preserve a meeting as source evidence and convert only reviewed, supported statements into proposed updates to current project state.

## Inputs

- Meeting note, transcript, or faithful summary
- Date, title, source identity, and project boundary
- Bounded index of current requirements, decisions, risks, assumptions, actions, changes, tests, and phase state
- Explicit reviewer disposition before any apply step

## Outputs

- One canonical meeting source record
- Candidate state changes with evidence references and confidence
- Human-readable review summary and machine-readable sidecar
- Optional approved updates to current records
- Processing result and unresolved questions

## Sequence

1. Preserve or create one canonical source record without changing its meaning.
2. Confirm project, scope, source identity, and confidentiality boundary.
3. Build a bounded current-state index; exclude unrelated projects and generated summaries.
4. Extract facts, proposed decisions, actions, risks, assumptions, requirements, validation evidence, and open questions.
5. Match each candidate to an existing stable ID or explain why a new record is needed.
6. Describe whether the candidate proposes a new record, a revision, closure or replacement, an evidence link, no state change, or manual review.
7. Validate structure, source support, lifecycle transition, and target compatibility.
8. Present a numbered approval summary with before/proposed-after views.
9. Record each approval, edit, rejection, or deferral and set a separate top-level apply gate.
10. Apply only approved candidates when source and target revisions still match.
11. Verify idempotency, relationships, provenance, and derived views.
12. Mark the intake item processed only after successful preservation and apply.

## State and status model

Track source intake from receipt through review and processing. Track each candidate from pending review to a recorded disposition and, when accepted, application. Route uncertainty explicitly to manual review. Current project records retain their own lifecycle models.

## Provenance and traceability

Each candidate cites a source section or time marker, target stable ID, match basis, confidence, reviewer disposition, and before/after state. The source note remains linked after apply. Duplicate application is prevented with a stable change identity or equivalent idempotency mechanism.

## Review and approval gates

- Interpretation is untrusted staging, even when schema-valid.
- Medium- or low-confidence matches require target verification.
- Every candidate receives an explicit disposition.
- Apply requires both per-candidate approval and a top-level approval.
- Changed source or target revisions invalidate the review and require regeneration.

## Adaptation

The source may come from chat, audio transcription, email, or a note system. Connector use is optional; the preservation, bounded-context, review, and apply semantics remain the same. Organizations may add candidate types without allowing free-form lifecycle transitions.

## Failure and uncertainty handling

Do not invent owners, dates, values, decisions, or approval. Ambiguity becomes an open question, assumption, or `needs_review` candidate. Conflicting statements remain separate. If project routing is uncertain, preserve the source in intake and stop before extraction or apply.
