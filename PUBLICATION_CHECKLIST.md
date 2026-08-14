# Publication Checklist

Complete this checklist manually before changing repository visibility, sharing an archive, publishing a release, or announcing Osito.

## Repository state

- [ ] The intended commit and branch are identified.
- [ ] The complete working-tree and staged diff have been reviewed.
- [ ] The complete Git history has been reviewed for sensitive or superseded content.
- [ ] No source repository history, remotes, reflogs, hooks, or submodules were inherited.
- [ ] No nested repositories, symlinks, hardlinks, archives, binaries, caches, logs, or temporary exports are present unexpectedly.
- [ ] Repository visibility is confirmed as private until every review is complete.

## Human content review

- [ ] Every tracked file has received a human review.
- [ ] Filenames, metadata, comments, examples, fixtures, and commit messages were reviewed.
- [ ] All examples are clearly labeled fictional.
- [ ] Fictional names, organizations, dates, identifiers, values, requirements, and results do not resemble a private source.
- [ ] No source paths, account identifiers, private domains, resource IDs, or distinctive terminology remain.
- [ ] Cross-file combinations were reviewed for re-identification risk.

## Privacy and security

- [ ] Local secret scans were run against tracked, untracked, and staged files.
- [ ] An external private denylist was scanned without copying it into the repository.
- [ ] Email, phone, address, account, token, key, connection-string, private-URL, and absolute-path patterns were reviewed.
- [ ] High-entropy findings and false-positive dispositions were manually reviewed.
- [ ] Hidden files, ignored files, large files, and generated artifacts were inspected.
- [ ] Optional unavailable scanners are recorded in the sanitization report.
- [ ] `SECURITY.md` directs suspected exposures away from public issues.
- [ ] If GitHub private vulnerability reporting is enabled, its instructions were checked for accuracy.
- [ ] No placeholder or invented security contact is published.

## Proprietary and licensing review

- [ ] No client, employer, supplier, commercial, or proprietary engineering information is present.
- [ ] No real dimensions, tolerances, calculations, test data, part numbers, costs, schedules, failures, or design rationale are present.
- [ ] Every file is newly written, safely reconstructed, or properly licensed and attributed.
- [ ] Paid standards, licensed specifications, books, third-party templates, and uncertain source material were excluded.
- [ ] The Apache License 2.0 remains appropriate for all included material.
- [ ] External links point to public, intended destinations and contain no private identifiers.

## Technical and documentation review

- [ ] Required-file and repository-structure tests pass.
- [ ] YAML and other structured examples parse successfully.
- [ ] Relative Markdown links resolve.
- [ ] Templates are nonempty and required placeholders are consistent.
- [ ] Duplicate identifiers and unexpected binary files were checked.
- [ ] POSIX and PowerShell setup instructions were tested where they differ.
- [ ] The fictional example works end to end.
- [ ] Claims about maturity, integrations, tests, and scanners are accurate.
- [ ] No documentation assumes access to a private system.

## Responsible AI and safety

- [ ] Documentation requires human review of AI output.
- [ ] The framework does not claim to replace engineering judgment, PLM/PDM, access control, or compliance processes.
- [ ] Safety-, legal-, regulatory-, security-, and quality-related limitations are visible.
- [ ] Prompts resist cross-project leakage and untrusted embedded instructions.
- [ ] Calculation and review workflows distinguish evidence, assumptions, results, and recommendations.

## Public profile and announcement

- [ ] Repository description and topics are accurate.
- [ ] Any public maintainer or security contact shown is intentional and usable; no placeholder contact is present.
- [ ] Organization profile, contributor metadata, and commit author information are suitable for public display.
- [ ] Pages, releases, packages, actions, applications, secrets, and collaborators are configured intentionally.
- [ ] Announcement copy has received separate privacy and claims review.
- [ ] A final repository-visibility check will be performed immediately after any authorized change.

## Approval

- Reviewer:
- Commit:
- Review date:
- Result: `approved | blocked`
- Blocking issues:
- Notes:

Approval of this checklist does not guarantee confidentiality or technical correctness. It records a diligent review at a specific repository state.

Set `Result` to `blocked` for any unresolved confidentiality, licensing, technical, or publication-review issue. Absence of optional GitHub private vulnerability reporting is not by itself a blocker.
