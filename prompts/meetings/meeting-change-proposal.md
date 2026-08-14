# Meeting State-Change Proposal

Use this prompt to extract reviewable project-state candidates from a preserved meeting source.

## Prompt

```text
Meeting source: <canonical source reference>
Project boundary: <project-key>
Meeting identity and date: <metadata>
Bounded current-state index: <record list or manifest>
Allowed candidate types: <types>

The meeting is source evidence, not current state and not approval.

1. Confirm the source identity and project routing.
2. Extract only statements supported by the source.
3. Separate facts, proposed decisions, actions, risks, assumptions, requirements, validation evidence, and open questions.
4. For each item, search the bounded index for an existing target before proposing a new record.
5. Describe whether each candidate proposes a new record, a revision, closure or replacement, an evidence link, no state change, or manual review.
6. Cite the source section or time marker and explain the match basis.
7. Do not infer owners, dates, decisions, status transitions, or approval.

Return:
## Processing summary
## Facts from the meeting
## Assumptions or ambiguous statements
## Numbered candidate changes

For every candidate include:
- candidate number
- change type
- record type
- target stable ID or NEW
- current state summary
- proposed state summary
- source reference
- rationale
- confidence
- conflict or ambiguity
- recommended reviewer disposition

## No-change items
## Open questions
## Proposed concise history entry
## Approval required

This output is an untrusted proposal. Do not edit canonical records. Ask the reviewer to approve, edit, reject, or defer each numbered candidate. Apply is a separate step requiring both candidate-level dispositions and explicit top-level authorization.
```
