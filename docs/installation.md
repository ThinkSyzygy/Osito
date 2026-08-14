# Installation

Osito is a repository of text files and local scripts. There is no system-wide installer and no required cloud service.

## Requirements

- Python 3.10 or newer for setup, validation, audit, and maintenance scripts
- Git for recommended version control and review
- A text editor

Optional tools may improve local secret scanning or authoring. Do not install an optional scanner merely because a workflow mentions it; review its source, license, and deployment policy first.

## Obtain the repository

### Git

POSIX shell:

```sh
git clone <repository-url> osito
cd osito
```

PowerShell:

```powershell
git clone <repository-url> osito
Set-Location osito
```

### Downloaded source archive

If a maintainer provides a reviewed archive, extract it into a new directory. Verify the archive source and checksum through a trusted channel. A source archive does not include Git history.

Do not place Osito inside an existing confidential project until its boundaries and ignore rules have been reviewed.

## Python environment

The supplied scripts are intended to use the Python standard library. A virtual environment is optional.

POSIX shell:

```sh
python -m venv .venv
. .venv/bin/activate
```

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell execution policy blocks a local script, follow your organization's policy. Do not weaken machine-wide policy simply to run Osito.

## Verify installation

```sh
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
```

Run the platform wrapper for local sanitization:

POSIX shell:

```sh
./scripts/audit/audit.sh
```

PowerShell:

```powershell
./scripts/audit/audit.ps1
```

Review findings; do not interpret an exit code as a confidentiality guarantee.

The audit reports link-like, reparse, unreadable, and observably changed entries without intentionally traversing their targets. Run it against a stable working tree with other writers stopped. It is not a transactional snapshot or a defense against a malicious writer; if the tree changes during inspection, stop other writers and rerun the audit.

## Filesystem support for apply operations

Project creation and archive apply are intended for a local workspace used by an individual or trusted small team. Stop other writers before applying changes. Existing destinations are preserved, and link-like or unsupported path structures stop the operation. The tools handle ordinary destination collisions and detect some unexpected changes; they do not defend against a malicious process or user that can modify the same tree during an operation.

Runtime validation for this release was performed on local NTFS on Windows, and Linux runtime validation was subsequently completed successfully. macOS remains untested and should be treated as unvalidated. Windows network paths and non-NTFS filesystems are unsupported. If required filesystem behavior is unavailable, apply stops without claiming success. Use project-creation dry run or archive preview and a recoverable checkpoint before apply. Treat a manual-inspection error as a stop condition rather than retrying automatically.

## Offline operation

Core authoring, setup, validation, and audit workflows are designed for local operation. Optional integrations may require network access, authentication, and additional review. None are configured by default.

## Upgrading

Before updating:

1. commit or back up local changes;
2. review the changelog and migration notes;
3. compare local templates and configuration with the new examples;
4. update schemas, scripts, and tests together;
5. rerun validation and audit in a sandbox;
6. obtain human approval before applying changes to operational projects.

During alpha development, incompatible changes are possible.
