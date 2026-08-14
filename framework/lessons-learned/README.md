# Lessons Learned

## Purpose

Convert reviewed experience into reusable guidance without exposing confidential context, blaming individuals, or treating one outcome as a universal rule.

## Inputs

- Project event, test, incident, review, or completed work
- Source evidence and original decision context
- Expected and observed outcomes
- Contributing conditions, attempted mitigations, and later evidence
- Confidentiality, ownership, and reuse constraints

## Outputs

- Lesson candidate with applicability and limitations
- Approved knowledge article or engineering principle
- Related process, checklist, training, risk, or action updates
- Review or retirement trigger

## Sequence

1. Select an event with enough evidence to support learning.
2. Describe expected and observed outcomes without assigning unsupported blame.
3. Separate observed facts, causal hypotheses, and unresolved questions.
4. Identify contributing system conditions and decision context.
5. Test whether the lesson generalizes beyond the original configuration.
6. State the principle, applicability, counterexamples, and failure modes.
7. Remove or abstract confidential and identifying details.
8. Review technical accuracy, ownership, and usefulness.
9. Approve promotion and link resulting process or training changes.
10. Revisit when new evidence challenges the lesson.

## State and status model

Suggested states are `candidate`, `analyzing`, `in_review`, `accepted`, `published`, `challenged`, `superseded`, and `retired`. A candidate is not team policy until accepted.

## Provenance and traceability

Keep private source links in the authorized system while the reusable article contains only safe, necessary attribution. Record the reviewer, approval date, scope of applicability, and records that implement the lesson.

## Review and approval gates

- Causal claims require evidence or must remain hypotheses.
- Publication requires confidentiality, ownership, licensing, and re-identification review.
- Changing a controlled process requires its own change approval.
- Safety-critical lessons receive qualified specialist review.

## Adaptation

Small teams can collect candidates during project retrospectives. Larger teams may use discipline-specific review boards. Keep examples fictional in public distributions and configure periodic review for fast-changing technologies.

## Failure and uncertainty handling

Do not generalize from a single event when context likely drove the outcome. Preserve competing explanations. If sanitization would leave a misleading lesson, retain it privately or omit it rather than over-redact it.
