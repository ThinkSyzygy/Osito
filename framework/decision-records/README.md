# Decision Records

## Purpose

Capture consequential engineering choices, considered alternatives, evidence, rationale, tradeoffs, and later supersession so teams do not repeatedly reconstruct why a direction was chosen.

## Inputs

- Decision question and decision owner
- Context, constraints, and applicable configuration
- Options considered, including the option to defer
- Evaluation criteria and supporting evidence
- Risks, assumptions, dependencies, and affected records

## Outputs

- Stable decision record
- Selected or deferred disposition
- Accepted tradeoffs and required follow-up
- Links to requirements, risks, actions, changes, tests, and superseded decisions

## Sequence

1. State the decision question and the latest useful decision date.
2. Define scope, constraints, and who has authority to decide.
3. Gather options and evidence; label assumptions and unknowns.
4. Compare options against explicit criteria.
5. Record dissent, uncertainty, and risks that would change the outcome.
6. Obtain the authorized disposition.
7. Link resulting actions, requirements, risks, and changes.
8. Monitor decision assumptions and review triggers.
9. If the decision changes, create a superseding record rather than rewriting history.

## State and status model

Suggested states are `proposed`, `under_review`, `accepted`, `deferred`, `rejected`, and `superseded`. A decision may also carry an implementation state such as `not_started`, `in_progress`, `validated`, or `failed`; keep this separate from whether the choice was approved.

## Provenance and traceability

Record source evidence, meeting or review references, decision authority, approval time, and affected configuration. Supersession links point in both directions. Facts, estimates, preferences, and assumptions are labeled separately.

## Review and approval gates

- Only the named authority may mark a decision accepted or reject an alternative on behalf of the project.
- Safety, compliance, financial, or cross-system decisions require the configured specialist reviewers.
- A decision based on unresolved assumptions identifies validation actions and a review trigger.
- Supersession requires an impact review of dependent requirements, risks, tests, and released artifacts.

## Adaptation

Use lightweight records for reversible local choices and fuller records for expensive or hard-to-reverse commitments. Configure approval roles by decision class rather than by document format.

## Failure and uncertainty handling

If authority is unclear, leave the decision under review. If evidence conflicts, preserve both positions and state what would resolve them. If no option is supportable, defer with a bounded next action instead of manufacturing consensus.
