# Calculation Review

## Purpose

Make engineering calculations reproducible, dimensionally consistent, independently checked, and clearly tied to the decision or requirement they support.

## Inputs

- Engineering question, applicable configuration, and decision context
- Governing equations and authorized references
- Inputs with units, sources, uncertainty, and value basis
- Assumptions, boundary conditions, simplifications, and exclusions
- Acceptance criteria and required margin
- Calculation implementation, if software or a spreadsheet is used

## Outputs

- Calculation note with equations and substituted values
- Result, uncertainty or sensitivity, and margin to criteria
- Independent-check record
- Limitations, unresolved inputs, and recommended validation
- Links to affected requirements, decisions, risks, and changes

## Sequence

1. State the question, output quantity, configuration, and acceptance criterion.
2. Define the physical model, control volume or boundary, sign convention, and units.
3. Cite governing equations and explain why they apply.
4. Inventory inputs and label measured, specified, calculated, estimated, and assumed values.
5. Check unit consistency and convert inputs explicitly.
6. Perform the calculation while retaining adequate internal precision.
7. Run limiting-case, order-of-magnitude, conservation, and sign checks as applicable.
8. Evaluate sensitivity to important inputs and identify dominant uncertainty.
9. Recompute independently using a second person, implementation, or derivation.
10. Compare with acceptance criteria and state the supported conclusion.
11. Obtain review and link any resulting action, risk, decision, or validation work.

## State and status model

Suggested states are `draft`, `inputs_incomplete`, `ready_for_check`, `checked`, `approved`, `failed_check`, `invalidated`, and `superseded`. Approval of the calculation does not by itself approve a design decision.

## Provenance and traceability

Record input sources and revisions, equation references, software or worksheet version, assumptions, intermediate results, precision policy, checker, and date. Preserve the exact reviewed implementation or a deterministic reproduction path.

## Review and approval gates

- Unknown model applicability, units, or acceptance criteria blocks approval.
- A material result requires an independent check.
- Safety, compliance, or high-consequence calculations require a qualified reviewer.
- Changes to inputs, equations, configuration, or implementation invalidate the prior approval until impact is checked.
- The downstream decision remains a separate approval.

## Adaptation

Add discipline-specific checklists for structural, thermal, fluid, optical, electrical, reliability, or statistical work. Automate calculations only after transparent reference cases pass and results remain inspectable.

## Failure and uncertainty handling

Do not hide nonconvergence, unstable sensitivity, or contradictory references. Report bounds when a point estimate is unjustified. If assumptions dominate the result, recommend measurement or testing before using the calculation for an irreversible commitment.
