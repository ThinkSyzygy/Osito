---
type: decision
id: DEC-ORION-001
project_id: ORION
status: accepted
owner: Alex Rowan
created: 2031-04-14
updated: 2031-04-14
fictional: true
source_links: ["../meetings/MTG-ORION-001.md"]
related_ids: [CHG-ORION-20310410-001, REQ-ORION-002, REQ-ORION-003, RSK-ORION-001]
supersedes: []
superseded_by: []
---

# Use a two-piece shell with passive side inlets

> **Fictional example:** the options, evidence, and decision are invented.

## Decision question

Which enclosure concept should the demonstration prototype use for air access and repeated rear service?

## Facts, assumptions, and constraints

- Fact: the charter excludes active airflow hardware.
- Fact: the circuit must remain accessible for bench work.
- Assumption: low rear inlets will remain clear on a flat desk; this is tracked as ASM-ORION-001.
- Constraint: the first build uses additively manufactured prototype parts.

## Options

| Option | Benefits | Costs and risks |
|---|---|---|
| Underside inlet | Visually quiet exterior | Most sensitive to desk obstruction |
| Side inlets plus removable rear cover | Easy to inspect and prototype | Visible openings; rear clearance still needs verification |
| Fan-assisted path | More controllable airflow | Adds hardware, noise, power, and scope excluded by the charter |

## Decision and rationale

Use passive inlets on both side walls and a removable rear cover retained by four same-type fasteners. This concept stays within scope, makes the air path visible during prototyping, and supports bench access.

## Consequences

- REQ-ORION-003 defines measurable desk clearance.
- RSK-ORION-001 remains open until the final foot geometry is checked.
- The decision does not establish sensor accuracy, response time, or product durability.

## Approval

Alex Rowan accepted the decision on 2031-04-14 after review by Morgan Vale. Revisit if active airflow becomes a requirement or the placement boundary changes.
