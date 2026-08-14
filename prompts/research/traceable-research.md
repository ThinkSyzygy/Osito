# Traceable Research Brief

Use this prompt for current, source-grounded research that may inform an engineering decision.

## Prompt

```text
Research question: <question>
Decision or work product supported: <context>
Scope and exclusions: <boundary>
Freshness requirement: <date or condition>
Permitted source classes: <sources>
Citation and licensing constraints: <constraints>

Do not broaden the question or import confidential context from another project.

1. Restate the question and define a stopping condition.
2. List prior facts, hypotheses, assumptions, and terms needing definition.
3. Gather permitted sources, preferring primary and authoritative material.
4. For each source, record authority, date or revision, applicability, freshness, and reuse limitations.
5. Build a claim-to-source map.
6. Separate directly supported facts from inference and recommendation.
7. Compare material conflicts without averaging incompatible claims.
8. Identify missing evidence and whether testing or specialist input is needed.
9. Check that quotations are minimal and lawful.

Return:
## Question and scope
## Source inventory
## Supported facts
## Conflicting evidence
## Inferences
## Assumptions and unknowns
## Findings by decision criterion
## Limitations and freshness
## Recommended next step
## Proposed knowledge or project updates
## Approval required

Do not approve or apply project changes. Promotion into reusable knowledge requires separate technical, confidentiality, ownership, and citation review. If the evidence is insufficient, state the boundary clearly and propose the smallest next inquiry or experiment.
```
