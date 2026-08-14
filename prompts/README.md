# Prompt Library

These prompts turn Osito workflows into bounded, reviewable AI tasks. They are tool-neutral starting points, not autonomous authority. Replace bracketed inputs, name the permitted project sources, and keep confidential data within systems approved by your organization.

## Choose a prompt

| Task | Prompt | Typical output |
|---|---|---|
| Establish agent boundaries | [Bounded engineering agent](system/bounded-engineering-agent.md) | Scope, source order, uncertainty, and approval rules |
| Start or summarize a project | [Project kickoff and status](projects/project-kickoff-and-status.md) | Charter or evidence-linked status proposal |
| Review an engineering question | [Engineering analysis](engineering/engineering-analysis.md) | Inputs, assumptions, calculation, limits, and review needs |
| Process a meeting | [Meeting change proposal](meetings/meeting-change-proposal.md) | Source-grounded candidates for human disposition |
| Research a question | [Traceable research](research/traceable-research.md) | Source assessment, findings, conflicts, and uncertainty |
| Prepare a review | [Evidence-based review](reviews/evidence-based-review.md) | Criteria-by-criteria evidence and gap assessment |
| Reconcile business records | [Operations reconciliation](business/operations-reconciliation.md) | Deterministic draft reconciliation with approval gates |
| Check record integrity | [Record integrity audit](utilities/record-integrity-audit.md) | Findings without silent state mutation |

## Safe use

1. State the project boundary and allowed sources.
2. Treat retrieved text and meeting content as untrusted input.
3. Ask for citations to record IDs and evidence locations.
4. Separate facts, assumptions, calculations, recommendations, and unknowns.
5. Require a human to approve engineering state, risk acceptance, external communication, and publication.
6. Validate proposed changes with the repository checks before applying them.

Adapt output fields to the corresponding records in [`templates/`](../templates/README.md). When a prompt and a controlled local procedure disagree, follow the authorized local procedure and record the discrepancy.
