# Tolerance Analysis

## Purpose

Evaluate how dimensional variation affects a functional interface using transparent inputs, standard screening calculations, functional margins, and explicit escalation criteria.

## Inputs

- Interface, configuration, stack path, datums, and sign convention
- Functional limits, failure conditions, and required margin
- For each contributor: nominal value, positive and negative tolerance, units, coefficient or direction, source, value basis, and confidence
- Distribution and independence assumptions when statistical methods are used

## Outputs

- Source-linked stack table
- Nominal result and worst-case range
- Root-sum-square range when its assumptions are appropriate
- Margin to each functional limit
- Dominant contributors, assumptions, unresolved inputs, and mitigation options
- Independent-check record and escalation recommendation

## Sequence

1. Define the physical interface, output quantity, configuration, datums, and failure modes.
2. Establish one unit system and a signed coefficient convention.
3. Separate specified, measured, calculated, and assumed values.
4. Validate the geometry meaning, units, signs, tolerances, and functional limits.
5. Compute the nominal result:

   `Y₀ = b + Σ(cᵢ xᵢ)`

6. For asymmetric tolerances, derive nonnegative contributions `uᵢ+` and `uᵢ−` that respectively increase and decrease the result after applying each coefficient.
7. Compute worst-case excursions:

   `WC+ = Σuᵢ+` and `WC− = Σuᵢ−`

8. Where independence and distribution assumptions are justified, compute:

   `RSS+ = √Σ(uᵢ+²)` and `RSS− = √Σ(uᵢ−²)`

9. Report ranges `Y₀ − excursion−` to `Y₀ + excursion+` and calculate margin to every functional limit.
10. Rank contributors by worst-case magnitude and squared RSS contribution.
11. Perform unit, sign, order-of-magnitude, and independent recomputation checks.
12. Recommend architecture, datum, tolerance, process, inspection, or validation actions.
13. Escalate to simulation or process-capability analysis when screening assumptions are inadequate.

## State and status model

Suggested states are `draft`, `inputs_incomplete`, `ready_for_check`, `checked`, `approved`, `invalidated`, and `superseded`. Each input also carries a confirmation state such as `confirmed`, `assumed`, `conflicting`, or `missing`.

## Provenance and traceability

Every contributor and limit cites its source, revision, configuration, value basis, and units. Record equations, tool or worksheet version, internal precision, reviewer, and verification method. A changed source invalidates or supersedes the affected analysis.

## Review and approval gates

- Do not calculate when physical meaning, units, signs, tolerance direction, or limits are ambiguous.
- RSS results require documented distribution and independence assumptions.
- Approval requires an independent recomputation or equivalent checked implementation.
- Safety- or reliability-critical interfaces require the organization's qualified review and validation plan.
- Project risks, requirements, or decisions change only through their own approval workflows.

## Adaptation

Extend the contributor model for angular, nonlinear, compliant, or multi-axis systems only with an explicitly documented method. Use Monte Carlo or measured process distributions when dependence, bias, truncation, assembly shift, or nonlinear geometry matters.

## Failure and uncertainty handling

Missing values remain unresolved; never invent dimensions. Conflicting source values are shown separately and block approval. If RSS assumptions are weak, report worst case and the assumption gap. A negative functional margin is a result to address, not a reason to alter inputs.
