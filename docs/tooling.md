# Local tooling

Osito's helper tools use only the Python standard library. They do not install dependencies, contact external services, approve engineering state, or publish content.

## Create a project

Preview the operation:

```sh
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional --dry-run
```

Create it:

```sh
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
```

POSIX and PowerShell wrappers are also provided:

```sh
./scripts/setup/create_project.sh --root . --project-id demo-project --name "Demo Project" --fictional
```

```powershell
.\scripts\setup\create_project.ps1 --root . --project-id demo-project --name "Demo Project" --fictional
```

The creator prefers `config/osito.local.yaml` and falls back to `config/osito.example.yaml` unless `--projects-dir` is supplied. It validates that the destination stays inside the repository, preserves any existing project destination, renders the charter and index templates in a temporary directory, and publishes the completed directory only after its checks pass. Add `--fictional` when creating an invented sandbox; operational projects default to `fictional: false`.

Apply is intended for an individual or trusted small team using a local workspace with other writers stopped. Link-like or unsupported path structures stop the operation. Local NTFS on Windows is the only apply environment runtime-tested for this release; Linux and macOS backends are present but unvalidated. Windows network paths and non-NTFS filesystems are unsupported. If required filesystem behavior is unavailable, apply stops without claiming success. Dry run remains available. See [Installation](installation.md#filesystem-support-for-apply-operations).

New projects default to `internal` classification and require human approval. Change the classification only after reviewing the applicable information-handling rules.

## Validate the repository

Run deterministic structural checks:

```sh
python scripts/validation/validate.py --root .
```

Validation covers required files and directories, template metadata and placeholders, the supported YAML subset, relative Markdown links, empty workflow areas, fictional-example labels and completeness, duplicate frontmatter IDs, binary files, symlinks, junctions, reparse points, nested repositories, the external-denylist interface, and repository-tree expectations. The validator prunes link-like and reparse entries before descending or reading their content and reports identity changes detected around file reads.

Exit code `0` means the implemented checks passed, `1` means validation findings exist, and `2` means validation could not start. Validation does not certify engineering correctness or publication safety.

Run the unit tests separately:

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

## Archive a project

Archiving is preview-only by default:

```sh
python scripts/maintenance/archive_project.py --root . --project-id demo-project
```

Review the reported source, destination, file count, preview manifest, and `preview_manifest_hash`. To apply the exact reviewed move, repeat the command with the approval phrase, the hash from that preview, and the human reviewer:

```sh
python scripts/maintenance/archive_project.py --root . --project-id demo-project --apply --approve ARCHIVE --reviewed-hash "<hash-from-preview>" --reviewer "Reviewer Name" --reason "Reviewed project closeout"
```

The archiver:

- checks the configured project and archive roots before and after the move;
- keeps the move inside configured repository roots;
- rejects nested project and archive roots, nested mounts, symbolic links, junctions, and reparse points;
- refuses existing destinations, including competing empty directories;
- never deletes or overwrites an archive;
- rejects apply when the reviewed preview hash no longer matches;
- verifies source disappearance, destination identity, containment, and content before recording success;
- writes the manifest through the retained moved-directory handle only after those checks pass;
- records the reviewer, reviewed hash, pre-archive content hash, and archive manifest;
- does not imply that retention, legal, contractual, or quality obligations have been satisfied.

Archive apply uses the same practical support boundary as project creation. Cleanup and rollback proceed only while the expected ownership, identity, and content can still be established. If recovery is ambiguous or could replace unrelated data, the tool stops for manual inspection and does not report success.

These controls address ordinary collisions and some detectable interference. They do not defend against a malicious process or user with write access to the same tree. Stop other writers before apply, use a recoverable checkpoint, and inspect any path named in a manual-inspection error before retrying.

Git remains the preferred history mechanism. Before archiving, close or explicitly disposition active records, link final evidence, complete the project closeout record, and obtain the required human approvals.
