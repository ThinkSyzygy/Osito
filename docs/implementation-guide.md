# Implementation Guide

This guide describes a staged adoption for an individual engineer or small team. Start with a fictional sandbox and add controls before confidential data.

## Phase 0: establish authority and ownership

Decide:

- who maintains the repository;
- who may approve project-state changes;
- where operational projects will live;
- which classifications are allowed;
- how access, backup, encryption, and recovery are handled;
- whether any AI service or connector is authorized;
- which laws, contracts, standards, and quality procedures apply.

Osito does not answer these organizational questions automatically.

## Phase 1: create a minimum viable workspace

Use the setup tool:

```sh
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
```

The example is fictional. Omit `--fictional` only when intentionally creating the first real project. Maintain only:

- project overview;
- requirements;
- decisions;
- risks and assumptions;
- actions;
- validation items;
- source meetings;
- engineering changes;
- phase status.

The setup tool creates the project directories, metadata, charter, and index. Add the first controlled records from [`templates/`](../templates/README.md) as the work requires them; it does not pre-populate empty requirements, decisions, or approvals.

Add other record families when they solve an observed problem.

### Acceptance criteria

- Every current record has a stable ID, project, status, classification, and source.
- The team knows which files are canonical.
- Generated content is clearly marked.
- A reviewer can find open risk, action, and validation state without reading every meeting.

## Phase 2: define lifecycle and review

Document allowed states and transitions for each record type. For example:

```text
proposed -> approved -> active -> completed
                   \-> rejected
active -> superseded
```

Do not use one universal status list if meanings differ. Define:

- who can propose;
- who can approve;
- what evidence is required;
- how closure is recorded;
- how supersession links old and new records;
- when a review becomes stale.

### Meeting workflow

Implement meeting ingestion as:

1. preserve a source note;
2. extract proposed changes;
3. validate identifiers and targets;
4. present each candidate for review;
5. apply approved candidates only;
6. record provenance and an idempotency key;
7. update a concise log;
8. leave rejected or uncertain items in review history.

Meeting discussion is not automatic approval.

## Phase 3: connect requirements to evidence

For every important requirement, define:

- source and rationale;
- measurable acceptance criteria;
- validation method;
- configuration and environment;
- owner;
- planned evidence;
- current disposition.

Link decisions, risks, tests, and changes by stable ID. A pass requires applicable evidence, not merely a checked box.

## Phase 4: introduce engineering reviews

Begin with a generic design review:

- architecture and interfaces;
- requirements coverage;
- risk and assumption state;
- manufacturing path;
- tolerance-sensitive interfaces;
- prototype and test evidence;
- open changes;
- documentation quality.

Classify findings by severity and assign an owner and closure condition. A review recommendation should not silently modify canonical state.

Add specialized reviews only where the product and risk justify them.

## Phase 5: introduce bounded AI assistance

Give an agent:

- root and project instructions;
- the selected project only;
- the smallest applicable workflow;
- explicit record IDs or subsystem scope;
- a clear output contract;
- no approval authority.

Require the agent to show unresolved inputs and sources. Use deterministic code for validation, arithmetic, IDs, hashes, and link checks where practical.

Test prompt-injection and cross-project leakage using fictional fixtures.

## Phase 6: automate local quality gates

Run:

```sh
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
python scripts/audit/sanitize.py --root .
```

Add an external denylist for publication or migration review:

```sh
python scripts/audit/sanitize.py --root . --denylist "$DENYLIST_PATH"
```

Keep automated results factual. A baseline can acknowledge reviewed debt but must not redefine an error as correct.

## Phase 7: add generated views

Create dashboards or compiled context only after canonical records are stable. Generated views should declare:

- scope;
- inputs;
- creation time;
- tool/config version;
- exclusions and warnings;
- freshness information.

Never edit a dashboard to correct source state.

## Phase 8: archive and improve

Before archiving:

- close or transfer actions;
- record final decisions and unresolved risks;
- link final evidence;
- mark current records terminal;
- preserve source material;
- confirm recovery.

Feed broadly useful, publication-safe lessons into shared methods only after ownership and confidentiality review.

## Operational definition of done

A workflow is complete when the intended artifact exists, provenance and approval are present, applicable tests pass, the diff is reviewed, generated views are refreshed when needed, and unresolved conflicts are reported.
