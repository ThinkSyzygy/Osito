# Traceable Engineering Analysis

Use this prompt for a bounded technical question, trade study, calculation, failure analysis, or prototype recommendation.

## Prompt

```text
Engineering question: <question>
Applicable configuration or revision: <configuration>
Project and subsystem boundary: <boundary>
Acceptance criteria or decision to support: <criteria>
Permitted sources: <source list>
Prohibited assumptions: <known constraints>

Analyze only the stated configuration and sources.

1. Define the physical problem, interfaces, units, sign conventions, and failure conditions.
2. Create separate lists of:
   - supported facts with source references;
   - assumptions with rationale and confidence;
   - inferences derived from facts;
   - unknowns that could change the result.
3. Explain the selected method and why it applies.
4. Show equations, substituted values, units, or comparison criteria when calculations are involved.
5. Run applicable unit, limiting-case, order-of-magnitude, sensitivity, and consistency checks.
6. Compare the result with the stated acceptance criteria.
7. Identify dominant contributors, limitations, and the smallest useful validation activity.

Return:
## Problem definition
## Facts and sources
## Assumptions
## Method
## Analysis and results
## Independent checks
## Sensitivity and limitations
## Supported conclusion
## Open questions
## Proposed validation or state changes
## Approval required

Do not invent missing engineering values. Do not approve a design, requirement, test result, risk disposition, or engineering change. If the model, units, geometry, inputs, or criteria are ambiguous, stop the affected calculation and return a precise input gap list.
```
