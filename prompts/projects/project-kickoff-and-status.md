# Project Kickoff or Current-State Brief

Use this prompt to create a proposed project record set or a concise current-state briefing.

## Prompt

```text
Mode: <kickoff | current-state brief>
Project: <project-key>
Audience or decision context: <audience>
Bounded sources: <approved source paths or record IDs>
Excluded context: <projects, folders, or systems not authorized>

Work only from the bounded sources. Do not search other projects. Treat generated views as navigation aids and verify material claims against canonical records.

For kickoff mode:
1. Extract the intended outcome, in-scope and out-of-scope work, stakeholders, constraints, success criteria, initial assumptions, initial risks, and expected lifecycle.
2. Separate supplied facts from proposed structure.
3. Identify missing authority, confidentiality, retention, and approval information.
4. Propose identity-neutral records and stable IDs, but do not create or approve them.

For current-state brief mode:
1. Identify the current project and readiness states from approved records.
2. Summarize active requirements, decisions, risks, assumptions, actions, changes, and validation relevant to the audience.
3. Deprioritize closed, superseded, canceled, stale, or explicitly paused work.
4. Preserve unresolved conflicts and missing evidence.

Return:
## Scope and source inventory
## Confirmed current facts
## Assumptions and open questions
## Proposed project overview or concise brief
## Top active risks and blockers
## Near-term actions and owners
## Conflicts, stale data, and missing categories
## Proposed record changes
## Explicit approvals needed

Do not change project state, assign authority, mark a gate ready, or close work. All record mutations remain proposals until explicitly approved.
```
