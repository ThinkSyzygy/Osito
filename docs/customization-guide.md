# Customization Guide

Osito is intended to be adapted. Customize terminology and structure while preserving the controls that make the system trustworthy.

## Preserve these invariants

- One explicit canonical home for each kind of current state
- Stable record identity
- Evidence linked separately from interpretation
- Review-before-apply for consequential changes
- Human approval that AI cannot self-assert
- Project boundary isolation
- Generated views marked noncanonical
- Visible assumptions, conflicts, and missing evidence
- Reversible lifecycle and migration behavior
- Local validation and privacy review

## Safe customization sequence

1. State the user problem.
2. Identify the current workflow and affected records.
3. Draft the new fields, states, or folder mapping.
4. Update documentation and configuration.
5. Update templates, scripts, and tests.
6. Create fictional positive and negative examples.
7. Plan migration for existing records.
8. Validate in a sandbox.
9. Obtain human approval.
10. Roll out incrementally and monitor.

## Folder layout

Teams may prefer one file per record, registers, or a hybrid. Consider:

- merge conflicts;
- record volume;
- link stability;
- ease of review;
- automation complexity;
- archive behavior;
- performance of the chosen editor.

Do not let layout make project boundaries ambiguous or turn generated content into source state.

## Record types

Add a record type only when it has:

- a distinct decision or maintenance purpose;
- a defined owner;
- lifecycle states;
- required provenance;
- a template;
- validation rules;
- a known relationship to existing records.

Avoid several files that track the same current fact.

## Status models

Use a small controlled vocabulary. Define allowed transitions and what evidence or approval each transition requires. Preserve old status meaning through migrations; do not reinterpret history silently.

## Templates

Templates should prompt for necessary reasoning without becoming forms that no one maintains. Test them by completing a fictional record.

When adapting a template:

- remove irrelevant fields;
- keep IDs, project, status, dates, classification, source links, and relationships;
- distinguish optional from required fields;
- provide neutral instructions rather than real examples;
- avoid copying a client or employer template.

## Phase gates

Replace generic gate names when an organization uses a different lifecycle. Criteria should remain evidence based. Define `unknown`, `not_applicable`, and accepted-risk handling rather than forcing every criterion into pass/fail.

## AI prompts

Keep prompts thin and task-specific. A prompt should route the agent to:

- applicable instructions;
- a shared workflow;
- defined input boundaries;
- a template or schema;
- validation;
- an output location or response format.

Do not store temporary project facts, credentials, or broad permissions in a reusable prompt.

## Integrations

Implement integrations behind a simple capability contract. Keep core workflows usable through local files. Separate read, draft, and irreversible write permissions, and require explicit approval for external effects.

See [Integrations](integrations.md).

## Branding

You may adapt organization-facing descriptions and visual identity subject to the license and applicable trademark rules. Do not imply endorsement, certification, or a capability the deployment does not have.

## Distribution

Before sharing a customized fork, complete a fresh licensing, privacy, security, example, history, and re-identification review. Customization often introduces the exact organization-specific details that a public repository must not contain.
