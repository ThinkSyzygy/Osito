# Getting Started

Osito supports two onboarding paths.

## AI-assisted onboarding

Recommended when you have an AI coding, desktop, or editor agent that can safely read and edit this local folder. Open [Start Here](../START_HERE.md) and tell the agent:

`Read START_HERE.md and onboard me to Osito.`

The agent follows the same local tools and safeguards documented below, but it asks only the questions needed for your setup, previews the plan, and waits for approval before writing.

## Manual onboarding

Use the steps below if you do not want AI assistance, your organization restricts AI use, you are troubleshooting, you maintain Osito, or you want to understand the commands the agent uses.

Use a fictional sandbox first. Do not begin by connecting Osito to confidential projects, mailboxes, drives, or chat systems.

## 1. Verify prerequisites

Recommended:

- Git
- Python 3.10 or newer
- A text editor

No note-taking application, cloud account, AI service, or external connector is required.

POSIX shell:

```sh
git --version
python --version
```

PowerShell:

```powershell
git --version
python --version
```

If `python` is not the correct command on your system, use the installed Python launcher consistently.

## 2. Clone or copy Osito

Use the repository location supplied by the maintainer.

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

Do not clone Osito into a confidential repository or copy a private repository into Osito.

## 3. Create local configuration

POSIX shell:

```sh
cp config/osito.example.yaml config/osito.local.yaml
```

PowerShell:

```powershell
Copy-Item config/osito.example.yaml config/osito.local.yaml
```

Review every setting. Keep organization-specific paths and classifications out of commits unless intentional. The local configuration file is ignored by default.

See [Configuration](configuration.md).

## 4. Run initial validation

```sh
python scripts/validation/validate.py --root .
```

The same command works in PowerShell:

```powershell
python scripts/validation/validate.py --root .
```

Then run the test suite:

```sh
python -m unittest discover -s tests -p 'test_*.py'
```

PowerShell:

```powershell
python -m unittest discover -s tests -p 'test_*.py'
```

## 5. Run the local audit

POSIX wrapper:

```sh
./scripts/audit/audit.sh
./scripts/audit/audit.sh --denylist "$DENYLIST_PATH"
```

PowerShell wrapper:

```powershell
./scripts/audit/audit.ps1
./scripts/audit/audit.ps1 -Denylist $DenylistPath
```

Portable Python entrypoint:

```sh
python scripts/audit/sanitize.py --root .
python scripts/audit/sanitize.py --root . --denylist "$DENYLIST_PATH"
```

Keep a real denylist outside the repository. Audit output can contain sensitive filenames or findings; handle it accordingly. See [Local auditing](local-auditing.md).

## 6. Create a fictional project

Preview the project plan first:

```sh
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional --dry-run
```

If the destination and file plan are correct, create it:

```sh
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
```

The commands are the same in PowerShell:

```powershell
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional --dry-run
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
```

Inspect every created file before adding real information. The `--fictional` flag records that this sandbox contains invented material; omit it only when intentionally creating an operational project under appropriate controls.

Creation apply prepares the complete project before publishing it, preserves any existing destination, and stops on link-like or unsupported path structures. Run it in a local workspace with other writers stopped, and inspect the dry-run before apply.

Apply operations were runtime-validated on local NTFS on Windows, and Linux runtime validation was subsequently completed successfully. macOS remains untested and should be treated as unvalidated. See [Installation](installation.md#filesystem-support-for-apply-operations) for the support boundary.

## 7. Try the core workflow

In the sandbox project:

1. write one fictional requirement;
2. record an assumption that affects it;
3. add a validation method and acceptance criterion;
4. capture a fictional meeting source note;
5. prepare proposed action and decision updates;
6. review and approve or reject each proposal as a human;
7. rerun validation.

This exercises the distinction between evidence, proposed interpretation, and approved current state.

## 8. If you add AI assistance, configure it carefully

Before giving an agent access:

- read the root `AGENTS.md`;
- restrict the agent to the sandbox project;
- disable external connectors unless explicitly needed and authorized;
- verify the model and service data-handling terms;
- require previews for writes;
- review every proposed change and diff;
- never allow the agent to approve its own work.

See [Responsible AI use](responsible-ai-use.md).

## 9. Plan real adoption

Do not import a private archive wholesale. Define classifications, ownership, project boundaries, backup and recovery, reviewer roles, and migration rules first.

Use the [Implementation guide](implementation-guide.md) and [Migration guide](migration-guide.md).

Before sharing any repository, rerun validation and the local audit, review every finding and diff, and complete the publication checklist. Passing the implemented checks is not approval for public release.
