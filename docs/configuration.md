# Configuration

Start from `config/osito.example.yaml`. The example is intentionally neutral and contains no credentials, real accounts, or private paths.

## Create a local file

POSIX shell:

```sh
cp config/osito.example.yaml config/osito.local.yaml
```

PowerShell:

```powershell
Copy-Item config/osito.example.yaml config/osito.local.yaml
```

The local file is ignored by default. Decide deliberately whether a sanitized organization-wide configuration should also be tracked.

The project-creation and archive tools prefer `config/osito.local.yaml` when it exists and otherwise fall back to the example file. Their minimal reader currently consumes only the workspace paths they need; other settings document policy and must be enforced by your local procedures or extensions.

## Repository settings

| Field | Purpose |
|---|---|
| `repository.repository_name` | Human-readable repository identifier |
| `repository.organization_name` | Public-safe organization label |
| `repository.default_timezone` | Timezone used when a workflow needs local time |
| `repository.default_date_format` | Display convention; ISO dates are recommended |

Do not put personal contact details or legal entity data into a public example.

## Workspace paths

`workspace` defines project, archive, generated, inbox, and template roots. Paths should be relative to the configured workspace wherever possible.

Avoid:

- user home directories;
- network-share credentials;
- project names that reveal clients;
- paths that traverse outside the intended workspace;
- symlinks that bypass project boundaries.

## Identity

Stable IDs decouple record identity from filenames. Choose a short, neutral project ID and never reuse a retired record ID.

If an organization already has controlled identifiers, document the mapping rather than embedding external account or database identifiers in every note.

## Governance

Recommended defaults:

- require human approval;
- require source links;
- preserve source evidence;
- keep generated content noncanonical;
- deny cross-project context;
- allow only shared framework and template roots.

Turning off a safeguard should require a documented reason and review.

## Features

Feature switches describe which workflows the workspace intends to use. They do not create access control or automatically install integrations.

Enable only the record families the team can maintain. A smaller current system is better than a large set of stale registers.

## Review behavior

`review` controls proposed-change defaults:

- new candidates begin pending;
- apply requires explicit approval;
- stale reviews are rejected;
- repeated apply should be idempotent.

Tools should fail closed when these expectations cannot be checked.

## Privacy

Define classification terms for the organization before real use. The included labels are examples, not a legal or regulatory policy.

`external_ai_allowed` and `external_connectors_allowed` default to false. Enabling them records intent but does not establish authorization. Review service terms, data location, retention, training use, administrators, and incident handling separately.

`denylist_path` should point to a file outside the repository or remain null. Never commit a private denylist.

## Integrations

Integration entries are disabled placeholders. Setting `enabled: true` does not create a working integration. Implement an adapter, store its credentials outside the repository, test it with fictional data, and document read/write behavior and approvals.

See [Integrations](integrations.md).

## Validation

Validation settings define local repository expectations, including broken links, metadata, fictional labeling, unexpected binaries, and maximum text-file size.

Validation does not determine whether an engineering conclusion is correct.

## Metadata

Record frontmatter follows [Metadata schema](../config/metadata-schema.md). When changing fields or statuses, update:

- schema documentation;
- machine-readable validation when present;
- every affected template;
- fictional examples;
- migration guidance;
- tests.

## Configuration review

Before using a configuration:

1. parse and validate it locally;
2. confirm every path stays inside the intended workspace;
3. confirm project and classification defaults;
4. inspect connector flags;
5. verify secrets are absent;
6. review it against organizational policy;
7. commit only the sanitized configuration intended for other users.
