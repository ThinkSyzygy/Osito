# Local auditing

Osito includes a dependency-free local audit for publication review. It checks text, filenames, and repository structure without sending content to a network service.

Automated checks cannot prove that a repository is confidential-data-free, correctly licensed, or safe to publish. Treat a passing result as one input to a manual review.

## Run the audit

From the repository root:

```sh
python scripts/audit/sanitize.py --root .
```

On POSIX systems, the wrapper selects an available Python 3 command without installing anything:

```sh
./scripts/audit/audit.sh --root .
```

On PowerShell:

```powershell
.\scripts\audit\audit.ps1 -Root .
```

The exit codes are:

- `0`: no automated findings;
- `1`: one or more findings;
- `2`: invalid arguments, unreadable configuration, or a missing runtime.

Use `--json` with the Python or POSIX entrypoint, or `-Json` with PowerShell, for machine-readable output.

## External denylist

Keep private names, domains, identifiers, and distinctive terms in a file outside the repository. Supply that file at runtime:

```sh
python scripts/audit/sanitize.py --root . --denylist <path-to-private-denylist>
```

```powershell
.\scripts\audit\audit.ps1 -Root . -Denylist <path-to-private-denylist>
```

Use one term per line. Blank lines and lines beginning with `#` are ignored. Matching is case-insensitive and covers both filenames and text content.

The audit never prints denylist entries or matched secret values. A filename containing a sensitive value is replaced with `<redacted-path>` in output. Do not commit the denylist, copy it into reports, or paste it into an issue.

## Checks performed

The local audit reports:

- denylist terms in names and text;
- non-example email addresses, phone-number patterns, and street-address patterns;
- private-key headers, credential assignments, service and cloud token patterns, and authenticated connection strings;
- absolute user or machine paths;
- private hosts, local network addresses, credential-bearing URLs, and resource, account, or policy identifiers;
- unusually high-entropy strings;
- binary, archive, oversized, hidden, and unexpected files;
- symbolic links, Windows junctions, general filesystem reparse points, hardlinks, nested Git repositories, submodule configuration, and unexpected top-level entries;
- unreadable entries and files whose filesystem identity changes while they are being inspected.

The scanner reports link-like and reparse entries without intentionally traversing their targets. It also reports unreadable entries and identity changes it observes. Run it against a stable working tree with other writers stopped. It is not a transactional snapshot or a defense against a malicious writer; if the tree changes during inspection, stop other writers and rerun the audit.

The email domains `example.com` and `example.org` are reserved for fictional public examples and do not produce an email finding.

## Detector-definition suppression

The scanner contains the patterns it detects. A narrow source-only marker prevents those pattern-definition lines from reporting themselves. The marker is honored only in `scripts/audit/sanitize.py`, does not suppress external-denylist matches, and is not a general waiver mechanism.

Do not add broad ignore rules to make a review pass. If a public example intentionally exercises a detector, construct the value at test runtime so the sensitive-looking literal is not stored in the repository.

## Optional local scanners

You may run additional secret scanners already approved and installed in your environment. Do not install tools automatically, upload the repository to a cloud scanner, or treat unavailable optional tools as having passed. Record each tool version, command, result, and unavailable check in the sanitization report.

## Limitations

Pattern matching can produce both false positives and false negatives. Entropy is only a heuristic. The audit cannot determine ownership, licensing, contractual restrictions, whether fictional content resembles a real project, or whether facts become identifying in combination.

Before publication, also inspect the complete staged diff, commit metadata, full Git history, ignored and untracked files, links, examples, and repository visibility. Complete `PUBLICATION_CHECKLIST.md` and obtain human approval.
