# Knowledge Architecture

## Purpose

Define where engineering information lives, which records are authoritative, how records relate, and how generated views are distinguished from evidence and current state.

## Inputs

- Team vocabulary and project boundaries
- Required record types and lifecycle states
- Existing repositories, document stores, and evidence locations
- Confidentiality, retention, and access requirements
- Search, automation, and reporting needs

## Outputs

- Repository or workspace map
- Record-type catalog and metadata schema
- Authority and precedence rules
- Relationship and naming conventions
- Generated-output policy
- Validation rules and onboarding guidance

## Sequence

1. Identify confidentiality boundaries before designing folders or indexes.
2. Inventory information by role: source evidence, approved current state, reusable knowledge, generated view, or historical material.
3. Define the minimum record types and a common metadata envelope.
4. Assign one canonical location and authority rule to each record type.
5. Define stable identifiers, controlled statuses, links, and supersession behavior.
6. Define how generated contexts, dashboards, and exports disclose their sources and freshness.
7. Add structural and relationship checks.
8. Test the architecture with a fictional project before migrating live material.
9. Document how records are created, reviewed, changed, closed, and archived.

## State and status model

The architecture distinguishes:

- **Source evidence:** received, normalized, or corrected; never treated as approved state by implication.
- **Current records:** draft, active, blocked, closed, rejected, or superseded according to type-specific rules.
- **Generated views:** fresh, stale, or invalid; never canonical.
- **Historical records:** closed, retired, or superseded and excluded from current-state summaries unless explicitly requested.

Status values should be centrally defined. Unknown status values fail validation rather than being guessed.

## Provenance and traceability

Every material claim should point to a source record, approved decision, or validated result. Relationships use stable IDs when possible. A generated view includes its generation time, input inventory or manifest, and freshness information. Corrections preserve the original source and explain the correction.

## Review and approval gates

- A human owner approves the record taxonomy and authority map.
- Moving authority from a legacy location to a new location requires a reviewed migration and rollback plan.
- Cross-project dependencies require explicit boundary approval.
- Baselines, suppressions, and schema changes require review because they change how correctness is interpreted.

## Adaptation

Folders are optional; the authority model is not. Small teams may use one file per register, while larger teams may use one file or database row per record. Preserve the same identity, lifecycle, provenance, and approval semantics across storage technologies.

## Failure and uncertainty handling

If two sources claim authority, stop and report the conflict. If a record lacks provenance, label it unverified. If a generated view is stale or cannot account for its inputs, regenerate it or do not use it. Never merge records solely because titles appear similar.
