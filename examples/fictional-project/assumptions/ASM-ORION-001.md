---
type: assumption
id: ASM-ORION-001
project_id: ORION
status: invalidated
owner: Morgan Vale
created: 2031-04-08
updated: 2031-04-21
fictional: true
source_links: ["../requirements/REQ-ORION-003.md", "../validation/VAL-ORION-001.md"]
related_ids: [RSK-ORION-001, ECN-ORION-001, VAL-ORION-001]
---

# Desk placement does not obstruct the rear inlet

> **Fictional example:** this assumption and its resolution are invented.

## Assumption

The original 1.8 mm rear foot height was assumed to keep the nearby inlet clear on an ordinary flat desk.

## Consequence if wrong

The prototype could violate REQ-ORION-003, and airflow observations could depend on how the enclosure was placed.

## Validation plan

Place the prototype on a flat reference plate, observe the lowest inlet edge, and measure the normal clearance.

## Resolution

The documented revision-A inspection in [VAL-ORION-001](../validation/VAL-ORION-001.md) found only 1.6 mm minimum clearance on 2031-04-21. The assumption was invalidated; it was not silently edited into a fact. The approved response is [ECN-ORION-001](../changes/ECN-ORION-001.md).
