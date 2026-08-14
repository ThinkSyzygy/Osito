# Glossary

## Agent adapter

A thin, tool-specific instruction that routes an AI agent to shared workflows, templates, schemas, and deterministic tools.

## Approval

An accountable human disposition authorizing a specific record or action at a known version. Approval is not inferred from authorship, discussion, or AI confidence.

## Assumption

An unverified statement being used temporarily, with an explanation of why it matters and how it will be tested.

## Baseline

A reviewed snapshot of known validation findings used to distinguish new debt. A baseline does not make a finding correct.

## Boundary

The permitted project, data class, source set, or external-system scope for a task.

## Canonical record

The designated source for current operational state.

## Change set

A reviewable collection of proposed creates, updates, closures, supersessions, or evidence additions.

## Classification

A handling label such as public, internal, confidential, or restricted. The organization defines and enforces its meaning.

## Compiled context

A bounded generated view assembled from approved records for a task. It is not a source of truth.

## Decision record

A record of a selected option, context, alternatives, rationale, effects, risks, and approval.

## Denylist

A private list of sensitive terms used during local sanitization. A real denylist remains outside the repository.

## Deterministic check

A repeatable rule whose result is derived from explicit inputs rather than AI judgment.

## Evidence

A source that supports, contradicts, or qualifies a claim. Evidence does not interpret or approve itself.

## Freshness

Whether the inputs, configuration, tool version, and arguments used to create a generated artifact still match current state.

## Generated view

A reproducible dashboard, context package, index, report, or export derived from canonical inputs.

## Human review

Meaningful evaluation by an accountable person, not merely opening a file or accepting an automated result.

## Idempotency

The property that safely repeating an apply operation does not duplicate or further change an already applied result.

## Lifecycle

The controlled states and transitions a record follows from proposal through approval, completion, rejection, retirement, or supersession.

## Manifest

A machine-readable account of inputs, outputs, inclusions, exclusions, versions, hashes, and warnings for a generated artifact.

## Operational state

The approved current requirements, decisions, risks, assumptions, actions, validation, changes, and status used to run a project.

## Project boundary

The records and shared dependencies a project workflow is permitted to access.

## Provenance

Information showing where a record or claim came from and how it changed.

## Re-identification

Inferring a private source, person, organization, or project from apparently sanitized details, especially combinations across files.

## Review staging

Noncanonical proposed material waiting for disposition.

## Risk acceptance

An explicit human decision to proceed with a known residual risk. It is not equivalent to leaving a risk unresolved.

## Source note

A preserved meeting, observation, import, or evidence record from which changes may be proposed.

## Stable ID

A repository-unique identifier that persists across filename, title, owner, and status changes.

## Suppression

A narrow, reviewed exception that changes how a finding is handled while keeping the raw finding visible.

## Supersession

An explicit relationship in which a newer record replaces an older record without deleting its history.

## Validation

Evidence-based confirmation that a requirement or rule is satisfied. Repository validation and product validation are distinct.
