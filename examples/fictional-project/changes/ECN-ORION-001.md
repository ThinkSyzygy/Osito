---
type: engineering_change
id: ECN-ORION-001
project_id: ORION
status: closed
owner: Morgan Vale
created: 2031-04-22
updated: 2031-05-02
fictional: true
source_links: ["../reviews/DR-ORION-001.md", "../validation/VAL-ORION-001.md"]
related_ids: [REQ-ORION-003, ASM-ORION-001, RSK-ORION-001]
---

# Increase rear support height

> **Fictional example:** the geometry, impacts, approvals, and verification are invented.

## Proposed change

Increase the nominal rear support height from 1.8 mm to 3.5 mm without changing inlet size, circuit location, or the front supports.

## Reason and evidence

The documented revision-A inspection in [VAL-ORION-001](../validation/VAL-ORION-001.md) measured only 1.6 mm clearance, below the 2.5 mm minimum in REQ-ORION-003. The invalidated assumption is recorded in ASM-ORION-001.

## Impact assessment

- Requirements: intended to restore compliance with REQ-ORION-003; other requirements unchanged.
- Stability: check that all four supports contact the reference surface.
- Manufacturing: update only the additive prototype model and build note.
- Cost and schedule: one replacement rear-shell print in the fictional plan.
- Documentation: update the prototype configuration and validation record.

## Risk and rollback

A taller rear support could introduce rocking if the front/rear heights are inconsistent. If flatness inspection fails, revert to revision A and evaluate relocating the inlet.

## Verification plan

Measure inlet clearance at four orientations and confirm stable four-point contact before closing the change.

## Approval and closure

Alex Rowan approved the change on 2031-04-24 after review by Morgan Vale. Fictional revision B was recorded on 2031-04-26. VAL-ORION-001 passed on 2031-05-02, and Morgan Vale closed the change that day.
