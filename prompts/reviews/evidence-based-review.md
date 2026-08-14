# Evidence-Based Review

Use this prompt for a design review, lifecycle gate, manufacturing review, readiness check, or structured gap analysis.

## Prompt

```text
Review type: <review>
Target decision or gate: <decision>
Project, subsystem, and configuration: <scope>
Criteria: <approved criteria list>
Evidence manifest: <bounded source list>
Review authority: <role, not assumed identity>

Evaluate each criterion independently. Missing evidence is unknown, not a pass.

1. Confirm scope, configuration, criteria, and authority.
2. Check evidence freshness, revision consistency, and provenance.
3. Separate facts, assumptions, interpretations, and unresolved conflicts.
4. Evaluate every criterion as pass, fail, partial, unknown, or not_applicable.
5. Cite evidence for pass, fail, and partial dispositions.
6. Identify blocking gaps, nonblocking gaps, accepted risks, and required actions.
7. Reconcile prior open findings and material changes.

Return:
## Review scope and evidence inventory
## Facts and assumptions
## Criterion table

Columns:
criterion | disposition | evidence | rationale | gap | owner/next action

## Blocking findings
## Nonblocking findings
## Accepted risks and approval references
## Evidence conflicts or stale inputs
## Recommended disposition
## Conditions and actions
## Approval required

The recommendation is advisory until the authorized reviewer approves it. Do not change phase, release, risk, finding, or requirement status. If criteria or configuration are ambiguous, provide a preparation gap list instead of a verdict.
```
