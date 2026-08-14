---
type: risk
id: RSK-ORION-001
project_id: ORION
status: mitigated
owner: Morgan Vale
created: 2031-04-14
updated: 2031-05-02
fictional: true
source_links: ["../meetings/MTG-ORION-001.md", "../validation/VAL-ORION-001.md"]
related_ids: [CHG-ORION-20310410-001, REQ-ORION-003, ASM-ORION-001, ECN-ORION-001]
---

# Desk placement may obstruct a low inlet

> **Fictional example:** the risk and assessment are invented.

## Risk statement

Because the rear inlet sits near the support surface, normal desk placement may reduce the intended geometric clearance, causing inconsistent prototype airflow observations.

## Assessment

The project uses a three-level qualitative scale defined only for this example.

- Initial likelihood: medium
- Initial consequence: medium
- Confidence: medium, because the first assessment preceded a physical build

These ordinal labels are prioritization aids, not probabilities.

## Trigger and response

- Trigger: measured clearance below REQ-ORION-003 or visible contact with the reference plate.
- Mitigation: inspect the prototype, then increase foot height if required.
- Contingency: relocate the rear inlet if increased feet do not preserve clearance across orientations.

## Residual risk

After ECN-ORION-001, the fictional final prototype measured 3.1 mm minimum clearance. Morgan Vale reviewed the evidence in VAL-ORION-001 and changed the status to `mitigated` on 2031-05-02. This does not validate sensor performance.
