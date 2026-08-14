# Metadata Schema

This document defines Osito's portable metadata contract. It is a documentation-level schema for Markdown frontmatter and JSON/YAML sidecars; implementations may add machine-readable schemas without changing these meanings.

## Design goals

- Stable identity across renames and moves
- Clear project ownership and confidentiality boundary
- Explicit lifecycle and approval state
- Source and relationship traceability
- Dates that sort and compare predictably
- Fields that remain understandable without a specific note-taking tool

## Common fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `type` | string | yes | Controlled record type |
| `id` | string | yes | Repository-unique stable identifier |
| `project_id` | string | yes for project records | Stable project identifier |
| `title` | string | recommended | Human-readable title when it cannot be reliably derived from the document heading |
| `status` | string | yes | Controlled lifecycle status |
| `created` | date | yes | ISO `YYYY-MM-DD` creation date |
| `updated` | date | yes | ISO `YYYY-MM-DD` last meaningful update |
| `owner` | string or null | recommended | Accountable role or fictional example person |
| `classification` | string | project root: yes | Information classification; child records may explicitly inherit the reviewed project classification |
| `source_links` | array of strings | yes | Relative links or source record IDs |
| `related_ids` | array of strings | yes | Stable IDs of related records |
| `tags` | array of strings | no | Search aids; never authority |
| `approved_by` | string or null | when approved | Reviewer identity or role |
| `approved_at` | timestamp or null | when approved | ISO-8601 approval time |
| `supersedes` | array of strings | no | IDs replaced by this record |
| `review_by` | date or null | no | Required next review date |

Use repository-relative paths. Do not store credentials, external resource tokens, local home paths, or private account identifiers in metadata.

## Identifier format

Recommended form:

```text
<TYPE>-<PROJECT_ID>-<SEQUENCE>
```

Examples below are fictional:

```text
REQ-demo-project-001
DEC-demo-project-004
RSK-demo-project-002
```

IDs do not change when a title, filename, owner, or status changes. Never reuse an ID after deletion or retirement.

## Controlled record types

Suggested starting values:

- `project_charter`
- `project_index`
- `project_closeout`
- `requirement`
- `decision`
- `risk`
- `assumption`
- `action`
- `meeting_source`
- `proposed_change_set`
- `prototype_plan`
- `test_plan`
- `test_result`
- `validation`
- `engineering_change`
- `calculation_review`
- `tolerance_analysis`
- `research_note`
- `lesson_learned`
- `design_review`
- `manufacturing_review`
- `phase_status`
- `business_intake`
- `invoice_data_preparation`
- `generated_context`
- `generated_report`

Teams may add types through a documented migration.

## Lifecycle status

Use record-type-specific controlled values. A small shared vocabulary is preferable:

- Working state: `draft`, `proposed`, `pending_review`, `planned`, `open`, `captured`
- Current state: `active`, `accepted`, `approved`, `in_progress`, `pass`, `verified`, `mitigated`
- Terminal state: `completed`, `closed`, `rejected`, `retired`, `superseded`, `invalidated`, `archived`
- Uncertainty: `needs_review`, `blocked`, `inconclusive`

Status meaning must be documented. A status is not evidence; approvals and sources remain explicit.

The included validator checks structural metadata but does not enforce every record-type transition. Before operational use, define local lifecycle tables and add tests for allowed transitions, required evidence, and approval roles.

## Information classification

The example configuration provides:

- `public`
- `internal`
- `confidential`
- `restricted`

Organizations must define these classes and their handling rules. Osito does not enforce access control.

## Approval fields

An agent may prepare a proposed record but must not populate approval fields as though a human approved it. Approval should identify:

- reviewer;
- timestamp;
- reviewed version or content hash when tooling supports it;
- scope of approval;
- unresolved exceptions.

## Example frontmatter

The following record is entirely fictional:

```yaml
---
type: decision
id: DEC-demo-project-004
project_id: demo-project
title: "Select the reversible latch concept for prototype B"
status: proposed
created: 2030-01-15
updated: 2030-01-15
owner: "role:mechanical-engineer"
classification: internal
source_links:
  - "../meetings/2030-01-14_concept-review.md"
related_ids:
  - RSK-demo-project-002
tags:
  - latch
approved_by: null
approved_at: null
---
```

## Relationships and provenance

- Use `source_links` for evidence or origin.
- Use `related_ids` for semantic relationships.
- Use `supersedes` only for explicit lifecycle replacement.
- Preserve original evidence even after a derived record changes.
- Generated records must include a generated marker and enough input information to assess freshness.

## Extension rules

Before adding or changing a field:

1. define its meaning and type;
2. identify every record type that uses it;
3. update templates, examples, validation, and migration guidance;
4. decide how older records behave;
5. avoid fields that duplicate current state elsewhere;
6. test that the change does not expose private data or tool-specific identifiers.
