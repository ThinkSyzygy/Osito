# Sanitization Summary

Check date: 2026-08-07

Scope: the complete `osito-open` private-staging candidate

Status: Windows-local practical remediation evidence is current. Human private-staging review remains incomplete, and this report does not claim public-release readiness.

This report records evidence gathered from the candidate repository itself. No private source vault or sibling project was accessed or compared, no package was installed, and no repository content was sent to a cloud scanner. Automated results support review; they do not prove confidentiality, correctness, licensing, or publication safety.

## Remediation completed

- Cleanup now isolates an expected temporary entry under a randomized quarantine name, revalidates identity and exact content or emptiness, and deletes only while ownership remains provable. Foreign or ambiguous replacements are preserved and reported for manual inspection.
- Project creation no longer reclaims a final published project name after an ambiguous outcome. It preflights an owned temporary tree before cleanup and leaves ambiguous content in place.
- Archive apply leaves the archive and manifest in place after confirmed or ambiguous manifest publication instead of attempting destructive rollback.
- Configuration and template inputs are opened once through pinned repository directories, without following link-like entries, and read as bounded strict UTF-8. Configuration is limited to 256 KiB and each template to 1 MiB.
- Input reads detect identity, name-binding, size, and metadata changes. Create and archive translate safe-read failures into their documented domain errors and do not report success.
- Documentation now states the practical Osito v0.1 boundary: an individual or trusted small team, a stable local workspace, and other writers stopped during operations. A malicious process or user continuously racing the same writable tree is outside this threat model.
- Security guidance directs suspected exposures away from public issues. GitHub private vulnerability reporting is recommended when available but optional; no placeholder contact is published, and absence of that feature alone is not a release blocker.
- Platform guidance identifies local NTFS on Windows as runtime-tested. Linux and macOS implementations remain unvalidated on this host.

## Local environment

- Windows PowerShell 5.1.26100.8875
- Git 2.53.0.windows.2
- Git Bash 5.2.37
- Python 3.12.13 from the existing bundled workspace runtime
- ripgrep 15.2.0

`PYTHONDONTWRITEBYTECODE=1` was set for Python validation and wrapper runs. The wrappers used their supported `PYTHON` override where the isolated shell did not otherwise expose Python. No dependency, cache, environment, build, or generated-output directory was intentionally created in the candidate.

## Test evidence

The pre-remediation baseline was 72 tests: 71 passed, 0 failed, and 1 was skipped because this Windows account lacks file-symlink privilege.

Final complete suite:

```text
python -m unittest discover -s tests -v
```

Result: 98 tests run; 94 passed; 0 failed; 4 skipped. The skips were the existing repository-link test and three raced template/configuration file-symlink tests, all due to Windows error 1314. Real Windows junction/reparse replacement and hardlink coverage ran and passed.

Final focused setup, archive, input-read, and cleanup suite:

```text
python -m unittest \
  tests.structure.test_setup_and_maintenance \
  tests.structure.test_safe_input_reads \
  tests.structure.test_conservative_cleanup -v
```

Result: 55 tests run; 52 passed; 0 failed; 3 file-symlink privilege skips.

The two new safety modules were then run ten consecutive times:

```text
python -m unittest \
  tests.structure.test_safe_input_reads \
  tests.structure.test_conservative_cleanup -q
```

Result across ten runs: 260 test executions; 230 passed; 0 failed; 30 expected privilege skips. Every run completed successfully.

Regression coverage includes normal cleanup, foreign file and directory replacements, empty and nonempty replacements, in-place mutation, mocked immediate identity reuse, disappeared and restored names, publication-temp replacement, foreign and relocated manifests, raced regular files, hardlinks, symlinks where supported, a file becoming a directory, oversized input, invalid UTF-8, post-open replacement, and in-place post-open mutation. Tests coordinate real filesystem state changes and assert resulting contents and paths.

## Validation and wrapper evidence

The bundled Python executable was used wherever these commands show `python`.

```text
python scripts/validation/validate.py --root .
python scripts/audit/sanitize.py --root .
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/audit/audit.ps1 -Root .
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup/create_project.ps1 --help
bash -lc 'scripts/audit/audit.sh'
bash -lc 'scripts/setup/create_project.sh --help'
python scripts/maintenance/archive_project.py --help
```

Results:

- deterministic repository validation passed;
- the built-in local audit passed with no findings;
- PowerShell audit and project-creation help wrappers passed;
- Git Bash audit and project-creation help wrappers passed with the bundled Python supplied through the wrapper-supported `PYTHON` variable;
- direct archive CLI help passed.

An initial isolated Git Bash wrapper attempt without the `PYTHON` override failed closed with its documented “Python 3 is required” message. The repository was not changed, and both wrappers then passed with the existing bundled runtime. No external denylist was supplied or accessed.

## Git and repository hygiene

The initial repository was an unborn `main` branch with 115 files already staged, 12,653 staged insertions, no unstaged changes, no untracked files, no remote, no refs or reflogs, and no submodule or Gitlink. The staged index listing had SHA-256 `b7961547e597b6e675d9679c479c8731db8a634a29d13c661d3ad340f17783c4`.

Initial object inspection found exactly 18 unreachable objects. Every one was a blob, and none was referenced by the index, a ref, or a reflog. Normal Git maintenance with immediate pruning removed the unreachable objects after the intended final tree was staged. Final full object inspection reports zero unreachable objects, and every staged blob remains readable. Index contents, status, and staged statistics were checked before and after maintenance.

Additional hygiene checks found:

- no configured remote;
- no commit or `HEAD` revision, as expected for the unborn branch;
- no submodule or Gitlink;
- no symbolic link, junction, or other reparse entry in the candidate working tree;
- only the repository-root `.git` directory;
- no `__pycache__`, `.pytest_cache`, `node_modules`, `dist`, or `build` directory;
- no unintended unstaged or untracked file after staging;
- clean staged and unstaged whitespace checks.

## Platform coverage

### Windows

The remediation was executed and tested on local NTFS on Windows. Passing coverage includes pinned-directory traversal, real junction rejection, destination-parent junction replacement, source and destination relocation, file identity and content checks, exclusive publication, competing destinations, manifest ambiguity, conservative cleanup, bounded input reads, and failure without false success.

The host can create junctions and hardlinks, and those tests passed. This account cannot create file symlinks, so four file-symlink tests were skipped honestly. Deterministic reparse and real junction tests remained active. Windows network paths and non-NTFS filesystems remain unsupported for apply operations.

### Linux and macOS

Linux and macOS backends are present but were not runtime-tested on this Windows host. Their destructive apply paths must be independently exercised in private staging before being described as supported. The POSIX equal-identity regression logic was reviewed but could not be executed here.

## Unavailable optional tools

The following optional local tools were unavailable and were not installed:

- gitleaks
- trufflehog
- detect-secrets
- semgrep
- git-secrets
- strings
- PowerShell 7 (`pwsh`)

Windows PowerShell 5.1 was available and its wrappers passed. An unavailable scanner is not counted as a passing scan.

## Limitations and required human work

The audit and validator are not transactional snapshots. They can report many link-like, unreadable, and changed entries, but they cannot prove safety against a malicious same-writer process that continuously changes and restores the tree between observations.

Cleanup isolation substantially narrows accidental replacement risk. POSIX does not provide a portable conditional-delete primitive, so a hostile writer that discovers and races a randomized quarantine name between final verification and deletion remains a theoretical residual risk outside the Osito v0.1 trusted-workspace threat model. Stop sync tools and other writers during operations. Treat any manual-inspection error as a stop condition and inspect the named repository-relative paths before retrying.

Automated checks cannot determine whether all facts are non-identifying in combination, whether examples resemble real work, whether every contribution is correctly licensed, whether future Git history is suitable for publication, or whether a workflow is appropriate for a specific organization.

Before any visibility change or publication, a human owner must:

1. review every file, filename, link, staged change, and any Git history;
2. confirm confidentiality boundaries, attribution, license rights, and fictional-example separation;
3. verify repository settings, integrations, collaborators, release surfaces, and any intentionally published contact;
4. complete `PUBLICATION_CHECKLIST.md`; and
5. obtain another independent private-staging practical audit at the exact candidate state.

GitHub private vulnerability reporting is recommended when available, but it is optional and its absence alone is not a blocker. Suspected exposure details must not be posted publicly.

## Current disposition

**READY FOR FINAL INDEPENDENT PRACTICAL AUDIT**

This means the bounded local remediation and deterministic checks passed. It does not authorize publication, change repository visibility, or replace human confidentiality and licensing review.
