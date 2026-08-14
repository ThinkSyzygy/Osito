# Record Integrity Audit

Use this prompt for a read-only semantic review of an Osito project or artifact set.

## Prompt

```text
Audit scope: <paths, records, or manifest>
Project boundary: <project-key>
Expected record types and status vocabularies: <schema references>
Checks requested: <structure, links, provenance, lifecycle, freshness, privacy>

Perform a read-only audit. Do not repair files, approve suppressions, or reinterpret policy.

Check:
1. Stable IDs are present and unique.
2. Record types and statuses use controlled values.
3. Required fields are present.
4. Source references and related IDs resolve within the authorized boundary.
5. Closed, rejected, retired, and superseded records are not presented as current.
6. Supersession and dependency links are consistent.
7. Generated views identify their inputs and freshness.
8. Material claims retain units, configuration, and evidence qualification.
9. Conflicting values remain visible.
10. No unrelated-project, private-path, credential-like, or identifying content appears in the reviewed export.

Return:
## Scope inspected
## Checks performed
## Facts
## Assumptions or policy ambiguities
## Findings table

Columns:
severity | rule | record | evidence | impact | proposed remediation

## Blocking findings
## Nonblocking findings
## Unresolved uncertainty
## Proposed fix plan
## Approval required

Findings are evidence, not permission to edit. Any fix plan is a proposal and must identify exact targets and expected changes. Semantic changes, baselines, suppressions, deletions, and cross-project moves require explicit human approval.
```
