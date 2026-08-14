# Osito record templates

Copy these files into a project and replace every `{{placeholder}}`. Do not edit a template in place to record project facts.

All canonical records use:

- a stable `id`;
- a `project_id`;
- a controlled `status`;
- an accountable `owner`;
- ISO `YYYY-MM-DD` dates;
- source and related-record links;
- explicit evidence, uncertainty, and approval fields.

Templates are starting points, not universal engineering requirements. Add fields that your quality system needs, but preserve stable identifiers and provenance.

| Area | Templates |
|---|---|
| Project | Charter, index, action, prototype, validation, and closeout records |
| Requirements | Requirement and assumption records |
| Engineering | Calculation review, engineering change, and tolerance analysis |
| Meetings | Source note and proposed change set |
| Decisions and risks | Decision and risk records |
| Reviews | Design and manufacturing reviews |
| Research and lessons | Research note and lesson learned |
| Business | Client intake and invoice-data preparation |

Before using a customized template, run `python scripts/validation/validate.py`.
