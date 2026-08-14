# Maintenance

Osito remains useful only when current records, templates, validation, and documentation evolve together.

## Every working session

- Put new source material in the correct project boundary.
- Record proposed changes separately from approved state.
- Update current records instead of adding another summary layer.
- Preserve source links and stable IDs.
- Close, retire, or supersede records explicitly.
- Review the diff before committing.

## Weekly review

- Open actions, blockers, and overdue reviews
- Assumptions awaiting validation
- High or changed risks
- Requirements without planned evidence
- Pending meeting and change-set reviews
- Generated views that are stale
- Repository status and backup health

Rebuild generated views only after approved canonical changes.

## Monthly review

- Access lists and connector permissions
- Classification and project-boundary configuration
- Restore-test status
- Stale decisions, accepted risks, and temporary exceptions
- Dependency and optional-tool updates
- Baseline and suppression review dates
- Broken links, duplicate identifiers, and orphaned evidence
- Public examples and documentation for accidental private additions

## Before a major review or release

Run:

```sh
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
python scripts/audit/sanitize.py --root .
```

When preparing content for sharing, add an external denylist:

```sh
python scripts/audit/sanitize.py --root . --denylist "$DENYLIST_PATH"
```

Review the complete output and diff. Record optional scanners that were unavailable. Complete the [Publication checklist](../PUBLICATION_CHECKLIST.md) for any public release.

## Adding a project

1. assign a neutral stable project ID;
2. configure its boundary and classification;
3. create the project from templates;
4. define local instruction differences only when necessary;
5. validate the empty structure;
6. add fictional smoke-test content before private data;
7. verify that searches and generated context do not include other projects.

## Adding or changing a record type

Update:

- metadata documentation and machine-readable schema;
- template;
- lifecycle and transition policy;
- validation;
- example;
- any generator or parser;
- migration notes;
- tests.

Do not reinterpret old records silently.

## Changing a workflow

Keep tool-specific adapters thin. Update the shared workflow first, then prompts, scripts, tests, examples, and operator documentation.

For consequential behavior, include:

- preview mode;
- explicit approval gate;
- freshness or hash checks;
- idempotent apply;
- destination-collision handling that preserves existing data;
- rollback or recovery;
- negative tests.

## Generated output

Generated output is disposable unless a policy explicitly designates a signed review artifact. Do not:

- edit it to correct canonical state;
- feed it into its own generation;
- treat an old report as current because it is polished;
- commit bulk output without a reason and review.

Delete disposable output only after confirming it can be regenerated and is not required evidence.

## Baselines and suppressions

A baseline records reviewed existing debt; it does not make the underlying condition correct. A suppression should be narrow and include rule, exact scope, rationale, owner, creation date, and review or expiry date.

AI agents must not approve baselines or suppressions.

## Archiving projects

Preview archival:

```sh
python scripts/maintenance/archive_project.py --root . --project-id demo-project
```

Apply requires the explicit approval token, the hash from the reviewed preview, and a human reviewer:

```sh
python scripts/maintenance/archive_project.py --root . --project-id demo-project --apply --approve ARCHIVE --reviewed-hash "<hash-from-preview>" --reviewer "Reviewer Name"
```

The example project ID is fictional. Before apply:

- resolve open actions;
- record remaining risk and ownership;
- link final evidence;
- mark lifecycle states;
- confirm destination and permissions;
- confirm the project tree contains no symbolic links, junctions, nested mounts, reparse points, or hardlinked files;
- review the preview;
- create a recoverable checkpoint.

Archive preserves history; it does not erase retention or confidentiality obligations.

Archive apply checks the configured roots and reviewed project tree, preserves any existing destination, and stops on link-like, changed, or unsupported path structures. After the move, it verifies source disappearance and archived content before writing `ARCHIVE_MANIFEST.json` and reporting success.

Cleanup and rollback are deliberately conservative. They proceed only while the expected ownership, identity, and content can still be established. If safe recovery is ambiguous or could replace unrelated data, the tool stops for manual inspection instead of deleting, moving, or claiming success.

These operations are intended for an individual or trusted small team using a local workspace. Stop other writers before preview and apply. Local NTFS on Windows is the only apply environment runtime-tested for this release; Linux and macOS backends are present but unvalidated. Windows network paths and non-NTFS filesystems are unsupported. See [Installation](installation.md#filesystem-support-for-apply-operations) for the full support boundary.

## Backup and recovery

Use a backup system appropriate to the data classification. Test restoration in an isolated location and verify canonical records, evidence, configuration, and external attachments. Git alone may not cover ignored or external files.

## Versioning

Record meaningful changes in `CHANGELOG.md`. During alpha, document breaking changes and migration steps explicitly. Tagging or releasing a version requires human approval and publication review.
