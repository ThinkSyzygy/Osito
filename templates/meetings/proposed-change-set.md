---
type: proposed_change_set
id: "CHG-{{project_id}}-{{date_compact}}-{{sequence}}"
project_id: "{{project_id}}"
status: pending_review
owner: "{{owner}}"
created: "{{date}}"
updated: "{{date}}"
source_links: ["{{meeting_id}}"]
related_ids: []
apply_permission: "not_granted"
---

# {{change_set_title}}

## Freshness

- Source hash:
- Current-state index hash:
- Processor or prompt version:
- Generated at:

Reject and regenerate this review if its source or target state changes.

## Candidates

### {{candidate_id}}

- Intended state effect and affected record:
- Record type:
- Existing target ID or `NEW`:
- Confidence:
- Evidence locator:
- Rationale:
- Conflict or ambiguity:
- Review status: `pending | approved | edited | rejected`

#### Before

Summarize the current machine-readable state or use `null`.

#### Proposed after

Show the complete proposed machine-readable state.

#### Reviewer edits

Record explicit edits without changing the source note.

## Apply gate

- [ ] A reviewer assigned a disposition to each proposed row.
- [ ] Uncertain record-identity mappings were not approved.
- [ ] Recorded source and target fingerprints still match current content.
- [ ] Repeating the operation would produce no additional state change.

- Reviewer:
- Reviewed at:
- `apply_permission`: `not_granted`
