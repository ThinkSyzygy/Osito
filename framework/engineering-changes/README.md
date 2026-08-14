# Engineering Changes

## Purpose

Control changes to approved requirements, designs, processes, software, tooling, tests, or documentation so impacts are understood before implementation and the released baseline remains traceable.

## Inputs

- Problem, opportunity, or originating request
- Current approved baseline and affected configuration
- Proposed change and alternatives
- Technical, safety, quality, cost, schedule, supply, and service impacts
- Required validation, implementation, communication, and rollback plans

## Outputs

- Engineering change request and disposition
- Approved implementation package
- Updated and superseded records
- Verification evidence and closure record
- Release or configuration update

## Sequence

1. Log the request with a stable ID, source, scope, and reason.
2. Triage urgency, affected configuration, authority, and whether containment is needed.
3. Identify impacted requirements, interfaces, decisions, risks, tests, parts, processes, and documentation.
4. Develop options, implementation steps, validation criteria, and rollback or recovery.
5. Review technical and business impacts with the required disciplines.
6. Approve, reject, defer, or request revision.
7. Implement only the approved revision and record actual deviations.
8. Verify the result against predefined criteria.
9. Update configuration and authority records, notify affected parties, and close.
10. Monitor for unintended consequences and reopen if necessary.

## State and status model

Suggested request states are `draft`, `submitted`, `analyzing`, `approved`, `rejected`, `deferred`, `implementing`, `verifying`, `closed`, and `canceled`. Implementation and verification are separate from approval. Superseded artifacts retain their identity and point to the replacing revision.

## Provenance and traceability

Preserve the originating source, before-state revision, impact analysis, reviewers, disposition, approved implementation, verification evidence, and affected configuration. Record emergency deviations and later formalization as linked events.

## Review and approval gates

- Analysis must cover all configured impact domains before approval.
- Only designated change authority can approve a baseline mutation.
- Implementation starts from an identified approved revision.
- Closure requires verification evidence and confirmation that dependent records were updated.
- Emergency changes require explicit emergency authority, containment, and retrospective review.

## Adaptation

Use a single lightweight path for reversible documentation changes and stricter paths for product, tooling, safety, compliance, or released-production changes. Configure reviewers and evidence by change class.

## Failure and uncertainty handling

Unknown impact keeps the request in analysis. Conflicting baselines stop implementation. If rollback is impossible, state that explicitly and increase review rigor. Partial or failed implementation triggers containment, preserves diagnostics, and does not advance to closed.
